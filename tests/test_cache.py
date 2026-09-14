from stock_predictor.core import cache
from stock_predictor.core.cache import TTLCache


def test_history_cache_expiration_and_capacity(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(cache, "monotonic", lambda: now[0])
    store = TTLCache(max_size=2, ttl_seconds=600)
    store.set("AAPL", 1)
    store.set("MSFT", 2)
    assert store.get("AAPL") == 1
    store.set("SPY", 3)
    assert store.get("MSFT") is None
    now[0] = 600
    assert store.get("AAPL") is None
    assert store.get("SPY") is None
