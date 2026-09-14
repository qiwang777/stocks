from datetime import datetime, timedelta, timezone

import pytest

from stock_predictor.app import create_app
from stock_predictor.core.config import Settings
from stock_predictor.schemas import Bar


@pytest.fixture
def app():
    return create_app(Settings(retraining_enabled=False, alpha_vantage_api_key="test-key"))


@pytest.fixture
def bars():
    return [
        Bar(
            time=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=index),
            open=price - 1,
            high=price + 1,
            low=price - 2,
            close=price,
            volume=1000 + index,
        )
        for index in range(80)
        for price in [100.0 + index * 0.2 + (2.0 if index % 2 else -2.0)]
    ]
