from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional

class Move(str, Enum):
    UP = "UP"
    DOWN = "DOWN"

class Bar(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class HistoryResponse(BaseModel):
    symbol: str
    interval: str
    bars: List[Bar]

class Prediction(BaseModel):
    symbol: str
    horizon: str
    as_of: datetime
    last_price: float
    predicted_move: Move
    confidence: float
    rationale: Optional[str] = None

class PredictionRequest(BaseModel):
    symbol: str
    horizon: str
