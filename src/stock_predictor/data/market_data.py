"""Provider selection, shared HTTP clients, history caching and quote polling."""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

import httpx

from stock_predictor.core.cache import TTLCache
from stock_predictor.data.providers.alpha_vantage import AlphaVantageProvider
from stock_predictor.data.providers.base import Provider
from stock_predictor.data.providers.eodhd import EodhdProvider
from stock_predictor.data.providers.finage import FinageProvider
from stock_predictor.data.providers.fmp import FmpProvider
from stock_predictor.data.providers.massive import MassiveProvider
from stock_predictor.data.providers.yahoo_finance import YahooFinanceProvider
from stock_predictor.schemas import HistoryResponse


class MarketDataClient:
    def __init__(
        self,
        av_base: str,
        av_key: str,
        provider: str = "alphaVantage",
        finage_base: str = "https://api.finage.co.uk",
        finage_key: str = "",
        cache_ttl_seconds: float = 600.0,
        cache_max_size: int = 500,
        timeout_seconds: float = 10.0,
        *,
        eodhd_base: str = "https://eodhd.com/api",
        eodhd_key: str = "",
        massive_base: str = "https://api.massive.com",
        massive_key: str = "",
        fmp_base: str = "https://financialmodelingprep.com/stable",
        fmp_key: str = "",
        quote_poll_seconds: float = 3.0,
    ):
        self.av_base = av_base.rstrip("/")
        self.av_key = av_key
        self.finage_base = finage_base.rstrip("/")
        self.finage_key = finage_key
        self.provider = provider.strip().lower()
        self.quote_poll_seconds = quote_poll_seconds
        self._timeout_seconds = timeout_seconds
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None
        self._history_cache: TTLCache[HistoryResponse] = TTLCache(
            max_size=cache_max_size, ttl_seconds=cache_ttl_seconds,
        )
        self._providers: dict[str, Provider] = {
            "alphavantage": AlphaVantageProvider(self, self.av_base, av_key),
            "finage": FinageProvider(self, self.finage_base, finage_key),
            "yfinance": YahooFinanceProvider(timeout_seconds),
            "eodhd": EodhdProvider(self, eodhd_base, eodhd_key),
            "massive": MassiveProvider(self, massive_base, massive_key),
            "fmp": FmpProvider(self, fmp_base, fmp_key),
        }
        if self.provider not in self._providers:
            raise ValueError(f"Unsupported market data provider: {self.provider}")

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
        return self._client

    @client.setter
    def client(self, value: httpx.Client) -> None:
        self._client = value

    @property
    def async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=self._timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
        return self._async_client

    @async_client.setter
    def async_client(self, value: httpx.AsyncClient) -> None:
        self._async_client = value

    def get_daily_history(self, symbol: str, range: str = "3mo") -> HistoryResponse:
        symbol = symbol.strip().upper()
        cache_key = (self.provider, symbol, range)
        cached = self._history_cache.get(cache_key)
        if cached is not None:
            return cached
        history = self._providers[self.provider].get_daily_history(symbol, range)
        history = history.model_copy(update={"data_source": [self.provider] if history.bars else []})
        if history.bars:
            self._history_cache.set(cache_key, history)
        return history

    def alpha_vantage_daily(self, symbol: str) -> HistoryResponse:
        return self._providers["alphavantage"].get_daily_history(symbol.strip().upper(), "3mo")

    def finage_daily(self, symbol: str, range: str = "3mo") -> HistoryResponse:
        return self._providers["finage"].get_daily_history(symbol.strip().upper(), range)

    def get_latest_price(self, symbol: str) -> str | None:
        return self._providers[self.provider].get_latest_price(symbol.strip().upper())

    async def get_latest_price_async(self, symbol: str) -> str | None:
        return await self._providers[self.provider].get_latest_price_async(symbol.strip().upper())

    def stream_prices(self, symbol: str):
        while True:
            price = self.get_latest_price(symbol)
            if price is not None:
                yield price
            time.sleep(self.quote_poll_seconds)

    async def stream_prices_async(
        self, symbol: str, poll_seconds: float | None = None,
    ) -> AsyncIterator[str]:
        delay = self.quote_poll_seconds if poll_seconds is None else poll_seconds
        while True:
            price = await self.get_latest_price_async(symbol)
            if price is not None:
                yield price
            await asyncio.sleep(delay)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    async def aclose(self) -> None:
        if self._async_client is not None:
            await self._async_client.aclose()

    def clear_cache(self) -> None:
        self._history_cache.clear()
