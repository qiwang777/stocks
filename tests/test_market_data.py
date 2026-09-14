import asyncio

import httpx
import pytest

from stock_predictor.data.market_data import MarketDataClient


def test_alpha_vantage_history_is_parsed_sorted_and_cached():
    calls = []

    def provider(request):
        calls.append(request)
        return httpx.Response(200, json={"Time Series (Daily)": {
            "2026-01-02": {"1. open": "102", "2. high": "103", "3. low": "101", "4. close": "102.5", "5. volume": "2000"},
            "2026-01-01": {"1. open": "100", "2. high": "101", "3. low": "99", "4. close": "100.5", "5. volume": "1000"},
            "2026-01-03": {"1. open": "102", "2. high": "103"},
        }})

    market = MarketDataClient("https://provider.test", "key")
    with httpx.Client(transport=httpx.MockTransport(provider)) as transport:
        market.client = transport
        first = market.get_daily_history("aapl")
        second = market.get_daily_history("AAPL")
    assert len(calls) == 1
    assert first == second
    assert [bar.close for bar in first.bars] == [100.5, 102.5]


def test_finage_daily_parses_aggregate_results():
    def provider(request):
        assert "/agg/stock/AAPL/1/day/" in request.url.path
        assert request.url.params["apikey"] == "key"
        return httpx.Response(200, json={"results": [
            {"o": 80.88, "h": 81.19, "l": 79.7375, "c": 80.3625, "v": 118746872, "t": 1580878800000}
        ]})

    market = MarketDataClient("https://provider.test", "", provider="finage", finage_key="key")
    with httpx.Client(transport=httpx.MockTransport(provider)) as transport:
        market.client = transport
        history = market.get_daily_history("aapl")
    assert len(history.bars) == 1
    assert history.bars[0].open == 80.88
    assert history.bars[0].volume == 118746872


@pytest.mark.parametrize("provider,payload,expected", [
    ("alphaVantage", {"Global Quote": {"05. price": "123.45"}}, "123.45"),
    ("finage", {"ask": 102, "bid": 100}, "101.0"),
])
def test_async_quote_polling(provider, payload, expected):
    async def check():
        market = MarketDataClient("https://provider.test", "key", provider=provider, finage_key="key")
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as transport:
            market.async_client = transport
            stream = market.stream_prices_async("aapl", poll_seconds=0)
            try:
                assert await anext(stream) == expected
            finally:
                await stream.aclose()

    asyncio.run(check())


def test_provider_http_failure_returns_empty_history():
    market = MarketDataClient("https://provider.test", "key")
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503))) as transport:
        market.client = transport
        assert market.get_daily_history("AAPL").bars == []
