from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient

from stock_predictor.schemas import DataSource, HistoryResponse


@pytest.mark.parametrize("source", list(DataSource))
def test_history_selects_source_and_reports_provenance(app, bars, monkeypatch, source):
    with TestClient(app) as client:
        market = app.state.market_data_by_source[source.value]
        calls = []

        def history(symbol, range_value):
            calls.append((symbol, range_value))
            return HistoryResponse(symbol=symbol, interval="1d", bars=bars)

        monkeypatch.setattr(market._providers[source.value], "get_daily_history", history)
        for _ in range(2):
            response = client.get("/api/v1/history", params={"symbol": "aapl", "datasource": source.value.upper()})
            assert response.status_code == 200
            assert response.json()["dataSource"] == [source.value]
            assert len(response.json()["bars"]) == len(bars)
        assert calls == [("AAPL", "3mo")]
        assert app.state.market_data.provider == "alphavantage"


@pytest.mark.parametrize("path,method", [
    ("/api/v1/history", "GET"), ("/api/v1/predict", "POST"), ("/api/v1/stream/quotes", "GET"),
])
@pytest.mark.parametrize("source", ["unknown", "", "   "])
def test_invalid_datasource_returns_422_before_fetching(app, path, method, source):
    with TestClient(app) as client:
        kwargs = {"params": {"symbol": "AAPL", "datasource": source}}
        if method == "POST":
            kwargs["json"] = {"symbol": "AAPL", "horizon": "1d"}
        response = client.request(method, path, **kwargs)
        assert response.status_code == 422
        assert response.json()["detail"][0]["loc"] == ["query", "datasource"]
        assert all(market._client is None for market in app.state.market_data_by_source.values())


@pytest.mark.parametrize("source", list(DataSource))
def test_stream_source_header_and_selection(app, monkeypatch, source):
    with TestClient(app) as client:
        selected = app.state.market_data_by_source[source.value]

        async def prices(symbol):
            assert symbol == "AAPL"
            yield "123.45"

        monkeypatch.setattr(selected, "stream_prices_async", prices)
        response = client.get("/api/v1/stream/quotes", params={"symbol": "AAPL", "datasource": source.value})
        assert response.status_code == 200
        assert response.headers["x-data-source"] == source.value
        assert response.text == "data: 123.45\n\n"
        assert app.state.market_data.provider == "alphavantage"


def test_concurrent_predictions_keep_models_and_history_separate(app, bars, monkeypatch):
    sources = ("fmp", "eodhd")
    with TestClient(app) as client:
        calls = {source: [] for source in sources}
        for index, source in enumerate(sources):
            offset = index * 100
            source_bars = [bar.model_copy(update={field: getattr(bar, field) + offset for field in ("open", "high", "low", "close")}) for bar in bars]

            def history(symbol, range_value, source=source, source_bars=source_bars):
                calls[source].append(symbol)
                return HistoryResponse(symbol=symbol, interval="1d", bars=source_bars)

            monkeypatch.setattr(app.state.market_data_by_source[source]._providers[source], "get_daily_history", history)

        def predict(source):
            response = client.post("/api/v1/predict", params={"datasource": source}, json={"symbol": "AAPL", "horizon": "1d"})
            assert response.status_code == 200
            return response.json()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(predict, sources))
        assert results[0]["lastPrice"] == bars[-1].close
        assert results[1]["lastPrice"] == bars[-1].close + 100
        assert [result["dataSource"] for result in results] == [["fmp"], ["eodhd"]]
        fmp_model = app.state.prediction_services["fmp"].models["AAPL"]
        eodhd_model = app.state.prediction_services["eodhd"].models["AAPL"]
        assert fmp_model is not eodhd_model
        predict("fmp")
        assert app.state.prediction_services["fmp"].models["AAPL"] is fmp_model
        assert calls == {"fmp": ["AAPL"], "eodhd": ["AAPL"]}
        assert app.state.prediction_service.models == {}
        assert app.state.scheduler.prediction_service is app.state.prediction_service


def test_default_source_and_short_history_provenance(app, bars, monkeypatch):
    with TestClient(app) as client:
        adapter = app.state.market_data._providers["alphavantage"]
        monkeypatch.setattr(adapter, "get_daily_history", lambda symbol, range_value: HistoryResponse(symbol=symbol, interval="1d", bars=bars[:5]))
        history = client.get("/api/v1/history?symbol=AAPL")
        prediction = client.post("/api/v1/predict", json={"symbol": "AAPL", "horizon": "1d"})
        assert history.json()["dataSource"] == ["alphavantage"]
        assert prediction.json()["dataSource"] == ["alphavantage"]


def test_empty_history_does_not_claim_a_contributing_source(app):
    with TestClient(app) as client:
        history = client.get("/api/v1/history?symbol=AAPL&datasource=massive")
        prediction = client.post("/api/v1/predict?datasource=massive", json={"symbol": "AAPL", "horizon": "1d"})
        assert history.json()["bars"] == []
        assert history.json()["dataSource"] == []
        assert prediction.json()["dataSource"] == []


def test_all_provider_http_clients_are_closed_on_shutdown(app):
    with TestClient(app):
        markets = app.state.market_data_by_source
        for market in markets.values():
            market.client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
            market.async_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    assert all(market.client.is_closed and market.async_client.is_closed for market in markets.values())


def test_openapi_exposes_datasource_for_every_endpoint(app):
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    assert schema["components"]["schemas"]["DataSource"]["enum"] == [source.value for source in DataSource]
    for path, method in (("/api/v1/history", "get"), ("/api/v1/predict", "post"), ("/api/v1/stream/quotes", "get")):
        parameters = schema["paths"][path][method]["parameters"]
        source = next(parameter for parameter in parameters if parameter["name"] == "datasource")
        assert source["in"] == "query" and source["required"] is False
