import pytest
from pydantic import ValidationError

from stock_predictor.core.config import Settings


def test_environment_settings_are_parsed_and_normalized(monkeypatch):
    monkeypatch.setenv("MARKETDATA_PROVIDER", "alphaVantage")
    monkeypatch.setenv("MODEL_RETRAIN_ENABLED", "false")
    monkeypatch.setenv("MODEL_RETRAIN_SYMBOLS", " aapl, , msft ")
    monkeypatch.setenv("PORT", "8090")
    settings = Settings.from_env()
    assert settings.market_data_provider == "alphavantage"
    assert settings.retraining_enabled is False
    assert settings.retraining_symbols == ("AAPL", "MSFT")
    assert settings.port == 8090


def test_invalid_cache_size_fails_at_configuration_time():
    with pytest.raises(ValidationError):
        Settings(cache_max_size=-1)


@pytest.mark.parametrize("provider", ["alphavantage", "finage", "yfinance", "eodhd", "massive", "fmp"])
def test_all_provider_names_are_supported(monkeypatch, provider):
    monkeypatch.setenv("MARKETDATA_PROVIDER", provider.upper())
    assert Settings.from_env().market_data_provider == provider


def test_new_provider_environment_variables(monkeypatch):
    for provider in ("EODHD", "MASSIVE", "FMP"):
        monkeypatch.setenv(f"MARKETDATA_{provider}_KEY", "test-key")
        monkeypatch.setenv(f"MARKETDATA_{provider}_BASE", f"https://{provider.lower()}.test")
    monkeypatch.setenv("MARKETDATA_POLL_SECONDS", "60")
    settings = Settings.from_env()
    for provider in ("eodhd", "massive", "fmp"):
        assert getattr(settings, f"{provider}_api_key") == "test-key"
        assert getattr(settings, f"{provider}_base_url") == f"https://{provider}.test"
    assert settings.quote_poll_seconds == 60


def test_unknown_provider_is_rejected():
    with pytest.raises(ValidationError):
        Settings(market_data_provider="unknown")
