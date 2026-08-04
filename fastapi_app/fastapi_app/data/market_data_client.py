from typing import List
import httpx
from fastapi_app.models import HistoryResponse, Bar
from datetime import datetime, timezone

class MarketDataClient:
    def __init__(self, av_base: str, av_key: str, provider: str = "alphaVantage"):
        self.av_base = av_base
        self.av_key = av_key
        self.provider = provider
        self.client = httpx.Client(timeout=10)

    def get_daily_history(self, symbol: str, range: str = "3mo") -> HistoryResponse:
        if self.provider.lower() == "finage":
            return HistoryResponse(symbol=symbol, interval="1d", bars=[])
        uri = f"{self.av_base}/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={self.av_key}"
        r = self.client.get(uri)
        if r.status_code != 200:
            return HistoryResponse(symbol=symbol, interval="1d", bars=[])
        body = r.json()
        series = body.get("Time Series (Daily)", {})
        bars = []
        for date_str, m in series.items():
            try:
                openS = m.get("1. open")
                highS = m.get("2. high")
                lowS = m.get("3. low")
                closeS = m.get("4. close")
                volS = m.get("5. volume")
                if None in (openS, highS, lowS, closeS, volS):
                    continue
                dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                bar = Bar(time=dt, open=float(openS), high=float(highS), low=float(lowS), close=float(closeS), volume=int(volS))
                bars.append(bar)
            except Exception:
                continue
        bars.sort(key=lambda b: b.time)
        return HistoryResponse(symbol=symbol, interval="1d", bars=bars)

    def stream_prices(self, symbol: str):
        # Simple polling generator; caller can wrap into SSE
        while True:
            uri = f"{self.av_base}/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.av_key}"
            r = self.client.get(uri)
            if r.status_code == 200:
                j = r.json()
                q = j.get("Global Quote")
                if q:
                    price = q.get("05. price")
                    if price:
                        yield price
            import time
            time.sleep(3)
