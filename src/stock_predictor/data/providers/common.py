from datetime import date, datetime, timedelta, timezone
from math import isfinite
from typing import Any, Iterable

from stock_predictor.schemas import Bar


def date_window(range_value: str) -> tuple[date, date]:
    end = datetime.now(timezone.utc).date()
    value = range_value.strip().lower()
    amount_text = "".join(char for char in value if char.isdigit())
    unit = "".join(char for char in value if not char.isdigit())
    amount = int(amount_text) if amount_text else 3
    if unit in {"d", "day", "days"}:
        days = amount
    elif unit in {"w", "wk", "week", "weeks"}:
        days = amount * 7
    elif unit in {"y", "yr", "year", "years"}:
        days = amount * 365
    else:
        days = amount * 30
    return end - timedelta(days=days), end


def parse_time(value: Any) -> datetime | None:
    try:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, (int, float)):
            seconds = value / 1000 if value > 10_000_000_000 else value
            parsed = datetime.fromtimestamp(seconds, tz=timezone.utc)
        else:
            text = str(value).strip()
            if text.isdigit():
                return parse_time(int(text))
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def make_bar(timestamp: Any, open_value: Any, high: Any, low: Any, close: Any, volume: Any) -> Bar | None:
    parsed = parse_time(timestamp)
    if parsed is None:
        return None
    try:
        prices = [float(value) for value in (open_value, high, low, close)]
        amount = float(volume)
        if not all(isfinite(value) for value in [*prices, amount]) or amount < 0:
            return None
        return Bar(time=parsed, open=prices[0], high=prices[1], low=prices[2], close=prices[3], volume=int(amount))
    except (TypeError, ValueError, OverflowError):
        return None


def sorted_bars(bars: Iterable[Bar | None]) -> list[Bar]:
    unique = {bar.time: bar for bar in bars if bar is not None}
    return sorted(unique.values(), key=lambda bar: bar.time)


def price_text(value: Any) -> str | None:
    try:
        number = float(value)
        return str(value) if isfinite(number) and number > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def first_present(row: dict, *names: str, default=None):
    return next((row[name] for name in names if row.get(name) is not None), default)


def named_bars(rows: Any) -> list[Bar]:
    if not isinstance(rows, list):
        return []
    return sorted_bars(
        make_bar(row.get("date"), row.get("open"), row.get("high"), row.get("low"), row.get("close"), row.get("volume"))
        for row in rows if isinstance(row, dict)
    )


def aggregate_bars(body: Any) -> list[Bar]:
    rows = body.get("results") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        return []
    return sorted_bars(
        make_bar(
            first_present(row, "t", "timestamp", "time", "date"),
            first_present(row, "o", "open"), first_present(row, "h", "high"),
            first_present(row, "l", "low"), first_present(row, "c", "close"),
            first_present(row, "v", "volume", default=0),
        ) for row in rows if isinstance(row, dict)
    )
