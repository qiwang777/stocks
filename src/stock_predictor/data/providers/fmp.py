from stock_predictor.data.providers.base import HttpProvider, RequestSpec
from stock_predictor.data.providers.common import date_window, named_bars, price_text


class FmpProvider(HttpProvider):
    def history_request(self, symbol, range_value):
        start, end = date_window(range_value)
        return RequestSpec(f"{self.base_url}/historical-price-eod/full", {
            "symbol": symbol, "apikey": self.api_key, "from": str(start), "to": str(end),
        })

    def quote_request(self, symbol):
        return RequestSpec(f"{self.base_url}/quote", {"symbol": symbol, "apikey": self.api_key})

    def parse_history(self, payload):
        return named_bars(payload)

    def parse_quote(self, payload):
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            return None
        return price_text(payload[0].get("price"))
