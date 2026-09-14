from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from stock_predictor.api.dependencies import get_market_data, get_prediction_service
from stock_predictor.app import create_app
from stock_predictor.core.config import Settings
from stock_predictor.schemas import Move, Prediction


def test_prediction_response_preserves_java_field_names(app):
    class FakePredictionService:
        def predict(self, symbol, horizon):
            return Prediction(
                symbol=symbol, horizon=horizon,
                asOf=datetime(2026, 1, 1, tzinfo=timezone.utc),
                lastPrice=123.45, predictedMove=Move.UP, confidence=0.75, rationale="ok",
            )

    app.dependency_overrides[get_prediction_service] = FakePredictionService
    with TestClient(app) as client:
        response = client.post("/api/v1/predict", json={"symbol": "AAPL", "horizon": "1d"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["asOf"] == "2026-01-01T00:00:00Z"
    assert payload["lastPrice"] == 123.45
    assert payload["predictedMove"] == "UP"
    assert "as_of" not in payload


@pytest.mark.parametrize("payload", [
    {"symbol": "   ", "horizon": "1d"},
    {"symbol": "AAPL", "horizon": ""},
    {"symbol": "AAPL"},
])
def test_predict_rejects_invalid_requests(app, payload):
    with TestClient(app) as client:
        assert client.post("/api/v1/predict", json=payload).status_code == 422


def test_history_and_real_prediction_share_cached_provider_data(app, bars):
    calls = []

    def provider(request):
        calls.append(request)
        return httpx.Response(200, json={"Time Series (Daily)": {
            bar.time.date().isoformat(): {
                "1. open": str(bar.open), "2. high": str(bar.high),
                "3. low": str(bar.low), "4. close": str(bar.close), "5. volume": str(bar.volume),
            } for bar in reversed(bars)
        }})

    with TestClient(app) as client:
        app.state.market_data.client = httpx.Client(transport=httpx.MockTransport(provider))
        history = client.get("/api/v1/history", params={"symbol": "aapl"})
        assert history.status_code == 200
        assert len(history.json()["bars"]) == len(bars)
        prediction = client.post("/api/v1/predict", json={"symbol": "aapl", "horizon": "1d"})
        assert prediction.status_code == 200
        result = prediction.json()
        assert result["symbol"] == "AAPL"
        assert result["lastPrice"] == bars[-1].close
        assert result["predictedMove"] in {"UP", "DOWN"}
        assert 0 <= result["confidence"] <= 1
        assert result["rationale"] == "Rationale unavailable."
        assert app.state.prediction_service.models["AAPL"].model is not None
        assert len(calls) == 1
        assert client.get("/docs").status_code == 200
        assert len(client.get("/openapi.json").json()["paths"]) == 3
    assert app.state.market_data.client.is_closed


def test_sse_quotes_have_correct_framing(app):
    class FakeMarketData:
        provider = "yfinance"

        async def stream_prices_async(self, symbol):
            assert symbol == "AAPL"
            yield "123.45"
            yield "123.50"

    app.dependency_overrides[get_market_data] = FakeMarketData
    with TestClient(app) as client:
        response = client.get("/api/v1/stream/quotes?symbol=AAPL")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-data-source"] == "yfinance"
    assert response.text == "data: 123.45\n\ndata: 123.50\n\n"


def test_lifespan_starts_and_stops_scheduler_without_sharing_services():
    first = create_app(Settings())
    second = create_app(Settings(retraining_enabled=False))
    with TestClient(first), TestClient(second):
        task = first.state.scheduler._task
        assert task is not None and not task.done()
        assert second.state.scheduler._task is None
        assert first.state.prediction_service is not second.state.prediction_service
    assert task.done()
    assert first.state.scheduler._task is None


@pytest.mark.parametrize("path", ["/api/v1/history", "/api/v1/stream/quotes"])
def test_blank_query_symbols_are_rejected(app, path):
    with TestClient(app) as client:
        assert client.get(path, params={"symbol": "   "}).status_code == 422
