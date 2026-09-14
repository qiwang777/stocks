from stock_predictor.data.providers.base import HttpProvider, RequestSpec
from stock_predictor.data.providers.common import make_bar, price_text, sorted_bars


class AlphaVantageProvider(HttpProvider):
    def history_request(self, symbol, range_value):
        return RequestSpec(f"{self.base_url}/query", {
            "function": "TIME_SERIES_DAILY", "symbol": symbol,
            "outputsize": "compact", "apikey": self.api_key,
        })

    def quote_request(self, symbol):
        return RequestSpec(f"{self.base_url}/query", {
            "function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self.api_key,
        })

    def parse_history(self, payload):
        series = payload.get("Time Series (Daily)") if isinstance(payload, dict) else None
        if not isinstance(series, dict):
            return []
        return sorted_bars(
            make_bar(day, row.get("1. open"), row.get("2. high"), row.get("3. low"), row.get("4. close"), row.get("5. volume"))
            for day, row in series.items() if isinstance(row, dict)
        )

    def parse_quote(self, payload):
        quote = payload.get("Global Quote") if isinstance(payload, dict) else None
        return price_text(quote.get("05. price")) if isinstance(quote, dict) else None
