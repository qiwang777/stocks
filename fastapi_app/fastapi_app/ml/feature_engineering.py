from typing import List, Tuple
import numpy as np
from fastapi_app.models import Bar
from math import sqrt


def build_dataset(bars: List[Bar]) -> Tuple[np.ndarray, np.ndarray]:
    if len(bars) < 25:
        return np.empty((0, 0)), np.empty((0,), dtype=int)
    feats = []
    labels = []
    for i in range(20, len(bars) - 1):
        f = features(bars, i)
        feats.append(f)
        today = bars[i].close
        nxt = bars[i + 1].close
        labels.append(1 if nxt > today else 0)
    X = np.array(feats)
    y = np.array(labels, dtype=int)
    return X, y


def features(bars: List[Bar], i: int):
    close = bars[i].close
    prev = bars[i - 1].close
    ret1 = (close - prev) / prev if prev != 0 else 0.0
    sma5 = sma(bars, i, 5)
    sma10 = sma(bars, i, 10)
    sma20 = sma(bars, i, 20)
    rsi14 = rsi(bars, i, 14)
    vol10 = volatility(bars, i, 10)
    return np.array([ret1, sma5 / close if close != 0 else 0.0, sma10 / close if close !=0 else 0.0, sma20 / close if close !=0 else 0.0, rsi14, vol10])


def sma(bars: List[Bar], i: int, w: int):
    s = 0.0
    for k in range(i - w + 1, i + 1):
        s += bars[k].close
    return s / w


def volatility(bars: List[Bar], i: int, w: int):
    m = sma(bars, i, w)
    s2 = 0.0
    for k in range(i - w + 1, i + 1):
        d = bars[k].close - m
        s2 += d * d
    return sqrt(s2 / w) / m if m != 0 else 0.0


def rsi(bars: List[Bar], i: int, period: int):
    gain = 0.0
    loss = 0.0
    for k in range(i - period + 1, i + 1):
        diff = bars[k].close - bars[k - 1].close
        if diff >= 0:
            gain += diff
        else:
            loss -= diff
    if loss == 0:
        return 1.0
    rs = (gain / period) / (loss / period)
    return rs / (1 + rs)
