"""Offline import, real model training, and API startup smoke check."""

import importlib
from pathlib import Path
import pkgutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from fastapi.testclient import TestClient

import stock_predictor
from stock_predictor.app import create_app
from stock_predictor.core.config import Settings
from stock_predictor.ml.logistic_model import DirectionModel


def main() -> None:
    modules = list(pkgutil.walk_packages(stock_predictor.__path__, stock_predictor.__name__ + "."))
    for module in modules:
        importlib.import_module(module.name)
    print(f"Imports: {len(modules)} modules OK")
    model = DirectionModel()
    model.fit(np.array([[-2.0], [-1.0], [1.0], [2.0]]), np.array([0, 0, 1, 1]))
    assert model.model is not None
    assert model.predict_proba(np.array([-2.0])) < 0.5 < model.predict_proba(np.array([2.0]))
    print("Logistic regression: two-class fit and prediction OK")
    with TestClient(create_app(Settings(retraining_enabled=False))) as client:
        response = client.get("/openapi.json")
        response.raise_for_status()
        assert len(response.json()["paths"]) == 3
        assert client.get("/docs").status_code == 200
    print("API: startup, OpenAPI, docs and shutdown OK (offline)")


if __name__ == "__main__":
    main()
