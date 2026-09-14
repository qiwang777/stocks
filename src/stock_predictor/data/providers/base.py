from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from stock_predictor.data.providers.common import sorted_bars
from stock_predictor.schemas import Bar, HistoryResponse


class Provider(Protocol):
    def get_daily_history(self, symbol: str, range_value: str) -> HistoryResponse: ...
    def get_latest_price(self, symbol: str) -> str | None: ...
    async def get_latest_price_async(self, symbol: str) -> str | None: ...


class HttpTransport(Protocol):
    @property
    def client(self) -> httpx.Client: ...

    @property
    def async_client(self) -> httpx.AsyncClient: ...


@dataclass
class RequestSpec:
    url: str
    params: dict[str, str | int]


class HttpProvider(ABC):
    def __init__(self, transport: HttpTransport, base_url: str, api_key: str):
        self.transport = transport
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()

    def get_daily_history(self, symbol: str, range_value: str) -> HistoryResponse:
        empty = HistoryResponse(symbol=symbol, interval="1d", bars=[])
        if not self.api_key:
            return empty
        request = self.history_request(symbol, range_value)
        bars = []
        visited = set()
        # Complete pagination before caching; never expose a partial failed download.
        for _ in range(100):
            identity = str(httpx.URL(request.url, params=request.params))
            if identity in visited:
                return empty
            visited.add(identity)
            payload = self.get_json(request)
            if payload is None:
                return empty
            bars.extend(self.parse_history(payload))
            try:
                request = self.next_history_request(payload)
            except ValueError:
                return empty
            if request is None:
                return HistoryResponse(symbol=symbol, interval="1d", bars=sorted_bars(bars))
        return empty

    def get_json(self, request: RequestSpec) -> Any:
        try:
            response = self.transport.client.get(request.url, params=request.params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError):
            return None

    def get_latest_price(self, symbol: str) -> str | None:
        if not self.api_key:
            return None
        return self.parse_quote(self.get_json(self.quote_request(symbol)))

    async def get_latest_price_async(self, symbol: str) -> str | None:
        if not self.api_key:
            return None
        request = self.quote_request(symbol)
        try:
            response = await self.transport.async_client.get(request.url, params=request.params)
            response.raise_for_status()
            return self.parse_quote(response.json())
        except (httpx.HTTPError, ValueError):
            return None

    def next_history_request(self, payload: Any) -> RequestSpec | None:
        return None

    @abstractmethod
    def history_request(self, symbol: str, range_value: str) -> RequestSpec: ...

    @abstractmethod
    def quote_request(self, symbol: str) -> RequestSpec: ...

    @abstractmethod
    def parse_history(self, payload: Any) -> list[Bar]: ...

    @abstractmethod
    def parse_quote(self, payload: Any) -> str | None: ...
