import asyncio
from datetime import datetime, timedelta, timezone
from threading import get_ident
from unittest.mock import Mock

import httpx
import pandas as pd
import pytest
import yfinance as yf
from fastapi.testclient import TestClient

from stock_predictor.app import create_app
from stock_predictor.core.config import Settings
from stock_predictor.data.market_data import MarketDataClient
from stock_predictor.data.providers.common import parse_time


REST_PROVIDERS = ["eodhd", "massive", "fmp"]


def market_client(provider, key="test-key"):
    return MarketDataClient(
        "https://provider.test", key, provider=provider,
        finage_key=key, eodhd_key=key, massive_key=key, fmp_key=key,
    )


def history_payload(provider, rows=None):
    rows = rows if rows is not None else [
        {"date": "2026-01-02", "open": 102, "high": 104, "low": 100, "close": 103, "volume": 2000},
        {"date": "2026-01-01", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000},
    ]
    if provider == "massive":
        return {"results": [
            {"t": int(datetime.fromisoformat(row["date"]).replace(tzinfo=timezone.utc).timestamp() * 1000),
             "o": row["open"], "h": row["high"], "l": row["low"], "c": row["close"], "v": row["volume"]}
            for row in rows
        ]}
    return rows


def quote_payload(provider):
    return {"eodhd": {"close": 123.45}, "massive": {"results": {"p": 123.45}}, "fmp": [{"price": 123.45}]}[provider]


@pytest.mark.parametrize("provider", REST_PROVIDERS)
def test_history_request_parsing_and_cache(provider):
    calls = []

    def handle(request):
        calls.append(request)
        query = request.url.params
        if provider == "eodhd":
            assert request.url.path == "/api/eod/AAPL.US"
            assert query["api_token"] == "test-key"
            assert query["fmt"] == "json" and query["period"] == "d"
        elif provider == "massive":
            assert request.url.path.startswith("/v2/aggs/ticker/AAPL/range/1/day/")
            assert query["apiKey"] == "test-key"
            assert query["adjusted"] == "false"
            start, end = request.url.path.rsplit("/", 2)[1:]
        else:
            assert request.url.path == "/stable/historical-price-eod/full"
            assert query["apikey"] == "test-key" and query["symbol"] == "AAPL"
        if provider != "massive":
            start, end = query["from"], query["to"]
        assert (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days == 30
        return httpx.Response(200, json=history_payload(provider))

    market = market_client(provider)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        market.client = client
        history = market.get_daily_history("aapl", "1mo")
        assert market.get_daily_history("AAPL", "1mo") == history
    assert len(calls) == 1
    assert history.symbol == "AAPL" and history.interval == "1d"
    assert [bar.close for bar in history.bars] == [101, 103]
    assert history.bars[0].time == datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("provider", REST_PROVIDERS)
def test_sync_and_async_quotes_use_correct_provider(provider):
    calls = []

    def handle(request):
        calls.append(request)
        path = {"eodhd": "/api/real-time/AAPL.US", "massive": "/v2/last/trade/AAPL", "fmp": "/stable/quote"}[provider]
        assert request.url.path == path
        key_name = {"eodhd": "api_token", "massive": "apiKey", "fmp": "apikey"}[provider]
        assert request.url.params[key_name] == "test-key"
        if provider == "fmp":
            assert request.url.params["symbol"] == "AAPL"
        return httpx.Response(200, json=quote_payload(provider))

    market = market_client(provider)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        market.client = client
        assert market.get_latest_price("aapl") == "123.45"

    async def check_stream():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            market.async_client = client
            stream = market.stream_prices_async("aapl", poll_seconds=0)
            try:
                assert await anext(stream) == "123.45"
            finally:
                await stream.aclose()

    asyncio.run(check_stream())
    assert len(calls) == 2


@pytest.mark.parametrize("provider", ["alphavantage", "finage", *REST_PROVIDERS])
def test_missing_key_does_not_create_clients_or_make_requests(provider):
    market = market_client(provider, key="")
    assert market.get_daily_history("AAPL").bars == []
    assert market.get_latest_price("AAPL") is None
    assert asyncio.run(market.get_latest_price_async("AAPL")) is None
    assert market._client is None and market._async_client is None


@pytest.mark.parametrize("provider", REST_PROVIDERS)
@pytest.mark.parametrize("payload", [None, {}, [], "denied", {"error": "invalid key"}])
def test_unexpected_payloads_do_not_crash(provider, payload):
    market = market_client(provider)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as client:
        market.client = client
        assert market.get_daily_history("AAPL").bars == []
        assert market.get_latest_price("AAPL") is None


@pytest.mark.parametrize("provider", REST_PROVIDERS)
@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_failed_history_is_not_cached(provider, status):
    responses = iter([httpx.Response(status), httpx.Response(200, json=history_payload(provider))])
    market = market_client(provider)
    with httpx.Client(transport=httpx.MockTransport(lambda request: next(responses))) as client:
        market.client = client
        assert market.get_daily_history("AAPL").bars == []
        assert len(market.get_daily_history("AAPL").bars) == 2


def test_massive_pagination_keeps_cursor_and_authentication():
    calls = []

    def handle(request):
        calls.append(request)
        assert request.url.params["apiKey"] == "test-key"
        if len(calls) == 1:
            payload = history_payload("massive")
            payload["next_url"] = "https://api.massive.com/v2/aggs/ticker/AAPL/range/1/day/2026-01-01/2026-01-02?cursor=next-page"
            return httpx.Response(200, json=payload)
        assert request.url.params["cursor"] == "next-page"
        return httpx.Response(200, json=history_payload("massive"))

    market = market_client("massive")
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        market.client = client
        history = market.get_daily_history("AAPL")
    assert len(calls) == 2
    assert len(history.bars) == 2


def test_massive_does_not_send_key_to_foreign_pagination_host():
    calls = []

    def handle(request):
        calls.append(request)
        payload = history_payload("massive")
        payload["next_url"] = "https://other.test/collect"
        return httpx.Response(200, json=payload)

    market = market_client("massive")
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        market.client = client
        assert market.get_daily_history("AAPL").bars == []
    assert len(calls) == 1


def test_eodhd_preserves_explicit_exchange_suffix():
    market = market_client("eodhd")
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[]))) as client:
        market.client = client
        adapter = market._providers["eodhd"]
        assert adapter.history_request("VOD.LSE", "3mo").url.endswith("/eod/VOD.LSE")


def test_yfinance_history_maps_timezone_raw_prices_and_cache(monkeypatch):
    frame = pd.DataFrame(
        {"Open": [102, 100, 1], "High": [104, 102, 2], "Low": [100, 99, 0],
         "Close": [103, 101, float("nan")], "Adj Close": [51.5, 50.5, 0], "Volume": [2000, 1000, 10]},
        index=pd.to_datetime(["2026-01-02", "2026-01-01", "2026-01-03"]).tz_localize("America/New_York"),
    )
    ticker = Mock()
    ticker.history.return_value = frame
    factory = Mock(return_value=ticker)
    monkeypatch.setattr(yf, "Ticker", factory)
    market = market_client("yfinance", key="")
    first = market.get_daily_history("aapl", "1mo")
    assert market.get_daily_history("AAPL", "1mo") == first
    factory.assert_called_once_with("AAPL")
    assert [bar.close for bar in first.bars] == [101, 103]
    assert first.bars[0].time.hour == 5
    arguments = ticker.history.call_args.kwargs
    assert arguments["auto_adjust"] is False and arguments["interval"] == "1d"
    assert (datetime.fromisoformat(arguments["end"]) - datetime.fromisoformat(arguments["start"])).days == 31


def test_yfinance_quotes_run_outside_event_loop(monkeypatch):
    threads = []

    def ticker(symbol):
        threads.append(get_ident())
        return Mock(fast_info={"last_price": 123.45})

    monkeypatch.setattr(yf, "Ticker", ticker)
    market = market_client("yfinance", key="")
    main_thread = get_ident()
    assert market.get_latest_price("AAPL") == "123.45"
    assert asyncio.run(market.get_latest_price_async("AAPL")) == "123.45"
    assert threads[0] == main_thread and threads[1] != main_thread


def test_yfinance_failure_and_invalid_quote(monkeypatch):
    ticker = Mock(fast_info={"last_price": float("nan")})
    ticker.history.side_effect = RuntimeError("unavailable")
    monkeypatch.setattr(yf, "Ticker", Mock(return_value=ticker))
    market = market_client("yfinance")
    assert market.get_daily_history("AAPL").bars == []
    assert market.get_latest_price("AAPL") is None


def test_invalid_timestamps_are_skipped_and_naive_dates_are_utc():
    assert parse_time(10**100) is None
    assert parse_time("2026-01-01") == datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("provider", REST_PROVIDERS)
def test_provider_wiring_through_api_to_real_prediction(provider, bars):
    rows = [{"date": bar.time.date().isoformat(), "open": bar.open, "high": bar.high,
             "low": bar.low, "close": bar.close, "volume": bar.volume} for bar in bars]
    settings = Settings(market_data_provider=provider, retraining_enabled=False, **{f"{provider}_api_key": "test-key"})
    app = create_app(settings)
    with TestClient(app) as client:
        app.state.market_data.client = httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=history_payload(provider, rows))
        ))
        response = client.post("/api/v1/predict", json={"symbol": "AAPL", "horizon": "1d"})
        assert response.status_code == 200
        assert response.json()["lastPrice"] == bars[-1].close
        assert app.state.prediction_service.models["AAPL"].model is not None
