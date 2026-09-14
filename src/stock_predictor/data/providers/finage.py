from urllib.parse import quote

from stock_predictor.data.providers.base import HttpProvider, RequestSpec
from stock_predictor.data.providers.common import aggregate_bars, date_window, first_present, price_text


class FinageProvider(HttpProvider):
    def history_request(self, symbol, range_value):
        start, end = date_window(range_value)
        return RequestSpec(
            f"{self.base_url}/agg/stock/{quote(symbol, safe='')}/1/day/{start}/{end}",
            {"apikey": self.api_key, "sort": "asc", "limit": 5000},
        )

    def quote_request(self, symbol):
        return RequestSpec(f"{self.base_url}/last/stock/{quote(symbol, safe='')}", {"apikey": self.api_key})

    def parse_history(self, payload):
        return aggregate_bars(payload)

    def parse_quote(self, payload):
        if not isinstance(payload, dict):
            return None
        value = price_text(first_present(payload, "price", "last", "p", "close"))
        if value is not None:
            return value
        ask, bid = price_text(payload.get("ask")), price_text(payload.get("bid"))
        if ask is not None and bid is not None:
            return price_text((float(ask) + float(bid)) / 2)
        return ask or bid
