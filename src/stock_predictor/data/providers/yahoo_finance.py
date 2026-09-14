import asyncio
from datetime import timedelta

from stock_predictor.data.providers.common import date_window, make_bar, price_text, sorted_bars
from stock_predictor.schemas import HistoryResponse


class YahooFinanceProvider:
    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def ticker(symbol):
        import yfinance as yf

        return yf.Ticker(symbol)

    def get_daily_history(self, symbol, range_value):
        start, end = date_window(range_value)
        bars = []
        try:
            # Yahoo's end date is exclusive. Do not mix adjusted close with raw OHLC.
            frame = self.ticker(symbol).history(
                start=str(start), end=str(end + timedelta(days=1)), interval="1d",
                auto_adjust=False, actions=False, timeout=self.timeout_seconds,
                raise_errors=True,
            )
            if frame is not None and not frame.empty:
                bars = sorted_bars(
                    make_bar(index.to_pydatetime(), row.get("Open"), row.get("High"),
                             row.get("Low"), row.get("Close"), row.get("Volume"))
                    for index, row in frame.iterrows()
                )
        except Exception:
            # yfinance raises several provider-specific transport and data errors.
            pass
        return HistoryResponse(symbol=symbol, interval="1d", bars=bars)

    def get_latest_price(self, symbol):
        try:
            return price_text(self.ticker(symbol).fast_info["last_price"])
        except Exception:
            return None

    async def get_latest_price_async(self, symbol):
        return await asyncio.to_thread(self.get_latest_price, symbol)
