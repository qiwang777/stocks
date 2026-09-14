from urllib.parse import quote, urljoin, urlsplit

import httpx

from stock_predictor.data.providers.base import HttpProvider, RequestSpec
from stock_predictor.data.providers.common import aggregate_bars, date_window, price_text


class MassiveProvider(HttpProvider):
    def history_request(self, symbol, range_value):
        start, end = date_window(range_value)
        return RequestSpec(f"{self.base_url}/v2/aggs/ticker/{quote(symbol, safe='')}/range/1/day/{start}/{end}", {
            "apiKey": self.api_key, "adjusted": "false", "sort": "asc", "limit": 50000,
        })

    def next_history_request(self, payload):
        next_url = payload.get("next_url") if isinstance(payload, dict) else None
        if not next_url:
            return None
        if not isinstance(next_url, str):
            raise ValueError("Invalid pagination URL")
        url = urlsplit(urljoin(self.base_url + "/", next_url))
        base = urlsplit(self.base_url)
        if (url.scheme, url.netloc) != (base.scheme, base.netloc):
            raise ValueError("Pagination must stay on the configured provider origin")
        params = dict(httpx.QueryParams(url.query))
        params["apiKey"] = self.api_key
        return RequestSpec(url._replace(query="", fragment="").geturl(), params)

    def quote_request(self, symbol):
        return RequestSpec(f"{self.base_url}/v2/last/trade/{quote(symbol, safe='')}", {"apiKey": self.api_key})

    def parse_history(self, payload):
        return aggregate_bars(payload)

    def parse_quote(self, payload):
        result = payload.get("results") if isinstance(payload, dict) else None
        return price_text(result.get("p")) if isinstance(result, dict) else None
