from fastapi_app.data.market_data_client import MarketDataClient
from fastapi_app.ml.feature_engineering import build_dataset, features
from fastapi_app.ml.smile_model import SmileModel
from fastapi_app.models import Prediction, PredictionRequest, HistoryResponse
from datetime import datetime, timezone
from typing import Dict
import numpy as np

class PredictionService:
    def __init__(self, market_client: MarketDataClient, rationale_service=None):
        self.market = market_client
        self.rationale = rationale_service
        self.models: Dict[str, SmileModel] = {}

    def train(self, symbol: str) -> SmileModel:
        hist: HistoryResponse = self.market.get_daily_history(symbol, "3mo")
        X, y = build_dataset(hist.bars)
        m = SmileModel()
        m.fit(X, y)
        self.models[symbol] = m
        return m

    def predict(self, symbol: str, horizon: str) -> Prediction:
        hist: HistoryResponse = self.market.get_daily_history(symbol, "3mo")
        bars = hist.bars
        X, y = build_dataset(bars)
        model = self.models.get(symbol)
        if model is None:
            m = SmileModel()
            m.fit(X, y)
            model = m
            self.models[symbol] = model
        if not bars:
            return Prediction(symbol=symbol, horizon=horizon, as_of=datetime.now(timezone.utc), last_price=0.0, predicted_move="UP", confidence=0.5, rationale=None)
        f = features(bars, len(bars) - 1)
        p_up = model.predict_proba(f)
        move = "UP" if p_up >= 0.5 else "DOWN"
        last = bars[-1].close
        rationale = None
        if self.rationale:
            rationale = self.rationale.explain(symbol, horizon, p_up, move, bars)
        return Prediction(symbol=symbol, horizon=horizon, as_of=datetime.now(timezone.utc), last_price=last, predicted_move=move, confidence=abs(p_up - 0.5) * 2, rationale=rationale)
