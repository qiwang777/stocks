from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from stock_predictor.jobs import retraining
from stock_predictor.jobs.retraining import RetrainingScheduler


@pytest.mark.parametrize("hour,minute,expected", [(8, 4, 60), (8, 5, 86400), (9, 5, 82800)])
def test_next_run_is_0805_utc(monkeypatch, hour, minute, expected):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, hour, minute, tzinfo=timezone.utc)

    monkeypatch.setattr(retraining, "datetime", FixedDateTime)
    assert RetrainingScheduler(Mock())._seconds_until_next_run() == expected


def test_daily_retraining_uses_default_symbols():
    service = Mock()
    service.retrain.return_value = {"AAPL": "trained"}
    scheduler = RetrainingScheduler(service)
    assert scheduler.retrain() == {"AAPL": "trained"}
    service.retrain.assert_called_once_with(["AAPL", "MSFT", "NVDA", "SPY"])
