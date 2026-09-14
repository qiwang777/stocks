from stock_predictor.data.market_data import MarketDataClient
from stock_predictor.ml.features import build_dataset, features
from stock_predictor.ml.logistic_model import DirectionModel
from stock_predictor.schemas import HistoryResponse, Move, Prediction
from datetime import datetime, timezone
from typing import Dict
from threading import RLock

class PredictionService:
    def __init__(self, market_client: MarketDataClient, rationale_service=None):
        self.market = market_client
        self.rationale = rationale_service
        self.models: Dict[str, DirectionModel] = {}
        self._lock = RLock()

    def train(self, symbol: str, force: bool = True) -> DirectionModel:
        symbol = symbol.strip().upper()
        if not force:
            with self._lock:
                cached = self.models.get(symbol)
            if cached is not None:
                return cached
        hist: HistoryResponse = self.market.get_daily_history(symbol, "3mo")
        X, y = build_dataset(hist.bars)
        m = DirectionModel()
        m.fit(X, y)
        with self._lock:
            self.models[symbol] = m
        return m

    def predict(self, symbol: str, horizon: str) -> Prediction:
        symbol = symbol.strip().upper()
        horizon = horizon.strip()
        hist: HistoryResponse = self.market.get_daily_history(symbol, "3mo")
        bars = hist.bars
        X, y = build_dataset(bars)
        with self._lock:
            model = self.models.get(symbol)
        if model is None:
            m = DirectionModel()
            m.fit(X, y)
            model = m
            with self._lock:
                self.models[symbol] = model
        if len(bars) < 21:
            last = bars[-1].close if bars else 0.0
            return Prediction(
                symbol=symbol,
                horizon=horizon,
                asOf=datetime.now(timezone.utc),
                lastPrice=last,
                predictedMove=Move.UP,
                confidence=0.5,
                dataSource=hist.data_source,
                rationale=None,
            )
        f = features(bars, len(bars) - 1)
        p_up = model.predict_proba(f)
        move = Move.UP if p_up >= 0.5 else Move.DOWN
        last = bars[-1].close
        rationale = None
        if self.rationale:
            rationale = self.rationale.explain(symbol, horizon, p_up, move, bars)
        return Prediction(
            symbol=symbol,
            horizon=horizon,
            asOf=datetime.now(timezone.utc),
            lastPrice=last,
            predictedMove=move,
            confidence=abs(p_up - 0.5) * 2,
            dataSource=hist.data_source,
            rationale=rationale,
        )

    def retrain(self, symbols: list[str]) -> dict[str, str]:
        results: dict[str, str] = {}
        for symbol in symbols:
            normalized = symbol.strip().upper()
            if not normalized:
                continue
            try:
                self.train(normalized, force=True)
                results[normalized] = "trained"
            except Exception as exc:
                results[normalized] = f"failed: {exc}"
        return results
