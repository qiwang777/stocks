"""Market bars and public API request/response schemas."""

from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from enum import Enum


NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DataSource(str, Enum):
    ALPHAVANTAGE = "alphavantage"
    FINAGE = "finage"
    YFINANCE = "yfinance"
    EODHD = "eodhd"
    MASSIVE = "massive"
    FMP = "fmp"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            return next((source for source in cls if source.value == normalized), None)
        return None


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)

class Move(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class Bar(ApiModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoryResponse(ApiModel):
    symbol: str
    interval: str
    bars: List[Bar]
    data_source: List[str] = Field(alias="dataSource", default_factory=list)


class Prediction(ApiModel):
    symbol: str
    horizon: str
    as_of: datetime = Field(alias="asOf")
    last_price: float = Field(alias="lastPrice")
    predicted_move: Move = Field(alias="predictedMove")
    confidence: float
    data_source: List[str] = Field(alias="dataSource", default_factory=list)
    rationale: Optional[str] = None


class PredictionRequest(ApiModel):
    symbol: NonBlankStr
    horizon: NonBlankStr
