import numpy as np

from stock_predictor.ml.features import build_dataset, features
from stock_predictor.ml.logistic_model import DirectionModel


def test_one_class_training_data():
    model = DirectionModel()
    model.fit(np.ones((5, 6)), np.ones(5, dtype=int))
    assert model.predict_proba(np.ones(6)) == 1.0


def test_real_two_class_training(bars):
    inputs, labels = build_dataset(bars)
    assert inputs.shape == (59, 6)
    assert set(labels) == {0, 1}
    model = DirectionModel()
    model.fit(inputs, labels)
    assert model.model is not None
    assert 0 <= model.predict_proba(features(bars, len(bars) - 1)) <= 1


def test_empty_training_data():
    model = DirectionModel()
    model.fit(np.empty((0, 6)), np.empty(0, dtype=int))
    assert model.predict_proba(np.ones(6)) == 0.5
