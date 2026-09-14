from unittest.mock import Mock

from stock_predictor.schemas import HistoryResponse
from stock_predictor.services.prediction import PredictionService


def test_short_history_does_not_raise_feature_error(bars):
    market = Mock()
    market.get_daily_history.return_value = HistoryResponse(symbol="AAPL", interval="1d", bars=bars[:5])
    prediction = PredictionService(market).predict("aapl", "1d")
    assert prediction.symbol == "AAPL"
    assert prediction.last_price == bars[4].close
    assert prediction.confidence == 0.5


def test_predictions_reuse_model_and_forced_training_replaces_it(bars):
    market = Mock()
    market.get_daily_history.return_value = HistoryResponse(symbol="AAPL", interval="1d", bars=bars)
    service = PredictionService(market)
    original = service.train("AAPL")
    assert service.train("aapl", force=False) is original
    service.predict("AAPL", "1d")
    assert service.models["AAPL"] is original
    assert service.train("AAPL", force=True) is not original


def test_retraining_continues_after_a_symbol_failure():
    service = PredictionService(Mock())
    service.train = Mock(side_effect=[RuntimeError("provider unavailable"), object()])
    result = service.retrain(["aapl", "MSFT"])
    assert result["AAPL"].startswith("failed:")
    assert result["MSFT"] == "trained"
    assert service.train.call_count == 2
