"""Validated settings loaded once when an application is created."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

from stock_predictor.schemas import DataSource


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=1, le=65535)
    market_data_provider: DataSource = DataSource.ALPHAVANTAGE
    alpha_vantage_base_url: str = "https://www.alphavantage.co"
    alpha_vantage_api_key: str = Field(default="", repr=False)
    finage_base_url: str = "https://api.finage.co.uk"
    finage_api_key: str = Field(default="", repr=False)
    eodhd_base_url: str = "https://eodhd.com/api"
    eodhd_api_key: str = Field(default="", repr=False)
    massive_base_url: str = "https://api.massive.com"
    massive_api_key: str = Field(default="", repr=False)
    fmp_base_url: str = "https://financialmodelingprep.com/stable"
    fmp_api_key: str = Field(default="", repr=False)
    quote_poll_seconds: float = Field(default=3.0, gt=0, allow_inf_nan=False)
    cache_ttl_seconds: float = Field(default=600.0, ge=0, allow_inf_nan=False)
    cache_max_size: int = Field(default=500, ge=0)
    retraining_enabled: bool = True
    retraining_symbols: tuple[str, ...] = ("AAPL", "MSFT", "NVDA", "SPY")
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = Field(default=0.2, ge=0, le=2)
    openai_base_url: str = "https://api.openai.com/v1"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(Path.cwd() / ".env", override=False)
        names = {
            "host": "HOST",
            "port": "PORT",
            "alpha_vantage_base_url": "MARKETDATA_AV_BASE",
            "alpha_vantage_api_key": "MARKETDATA_AV_KEY",
            "finage_base_url": "MARKETDATA_FINAGE_BASE",
            "finage_api_key": "MARKETDATA_FINAGE_KEY",
            "eodhd_base_url": "MARKETDATA_EODHD_BASE",
            "eodhd_api_key": "MARKETDATA_EODHD_KEY",
            "massive_base_url": "MARKETDATA_MASSIVE_BASE",
            "massive_api_key": "MARKETDATA_MASSIVE_KEY",
            "fmp_base_url": "MARKETDATA_FMP_BASE",
            "fmp_api_key": "MARKETDATA_FMP_KEY",
            "quote_poll_seconds": "MARKETDATA_POLL_SECONDS",
            "cache_ttl_seconds": "CACHE_TTL_SECONDS",
            "cache_max_size": "CACHE_MAX_SIZE",
            "retraining_enabled": "MODEL_RETRAIN_ENABLED",
            "openai_api_key": "OPENAI_API_KEY",
            "openai_model": "OPENAI_MODEL",
            "openai_temperature": "OPENAI_TEMPERATURE",
            "openai_base_url": "OPENAI_BASE_URL",
        }
        values = {field: os.environ[name] for field, name in names.items() if name in os.environ}
        aliases = {
            "finage_api_key": "FINAGE_API_KEY",
            "openai_api_key": "SPRING_AI_OPENAI_API_KEY",
            "openai_model": "SPRING_AI_OPENAI_CHAT_OPTIONS_MODEL",
        }
        for field, name in aliases.items():
            if field not in values and name in os.environ:
                values[field] = os.environ[name]
        values["market_data_provider"] = os.getenv("MARKETDATA_PROVIDER", "alphavantage").strip().lower()
        if "MODEL_RETRAIN_SYMBOLS" in os.environ:
            values["retraining_symbols"] = tuple(
                symbol.strip().upper()
                for symbol in os.environ["MODEL_RETRAIN_SYMBOLS"].split(",")
                if symbol.strip()
            )
        return cls.model_validate(values)
