from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from time import monotonic
from typing import Generic, Hashable, Optional, TypeVar


T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, max_size: int = 500, ttl_seconds: float = 600.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = RLock()
        self._items: OrderedDict[Hashable, tuple[float, T]] = OrderedDict()

    def get(self, key: Hashable) -> Optional[T]:
        now = monotonic()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= now:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: Hashable, value: T) -> None:
        expires_at = monotonic() + self.ttl_seconds
        with self._lock:
            self._items[key] = (expires_at, value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_size:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
