from urllib.parse import quote

from stock_predictor.data.providers.base import HttpProvider, RequestSpec
from stock_predictor.data.providers.common import date_window, named_bars, price_text


class EodhdProvider(HttpProvider):
    @staticmethod
    def ticker(symbol):
        # EODHD requires an exchange suffix. Explicit provider-native tickers win.
        return symbol if "." in symbol else f"{symbol}.US"

    def history_request(self, symbol, range_value):
        start, end = date_window(range_value)
        return RequestSpec(f"{self.base_url}/eod/{quote(self.ticker(symbol), safe='')}", {
            "api_token": self.api_key, "fmt": "json", "period": "d", "order": "a",
            "from": str(start), "to": str(end),
        })

    def quote_request(self, symbol):
        return RequestSpec(f"{self.base_url}/real-time/{quote(self.ticker(symbol), safe='')}", {
            "api_token": self.api_key, "fmt": "json",
        })

    def parse_history(self, payload):
        return named_bars(payload)

    def parse_quote(self, payload):
        return price_text(payload.get("close")) if isinstance(payload, dict) else None
