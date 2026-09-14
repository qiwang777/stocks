from typing import Any, Optional

import numpy as np

class DirectionModel:
    def __init__(self):
        self.model: Optional[Any] = None
        self.constant_probability: Optional[float] = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model = None
        self.constant_probability = None
        if X.size == 0 or y.size == 0:
            self.constant_probability = 0.5
            return
        unique = np.unique(y)
        if unique.size < 2:
            self.constant_probability = float(unique[0])
            return
        from sklearn.linear_model import LogisticRegression

        if not np.isfinite(X).all():
            self.model = None
            self.constant_probability = 0.5
            return
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X, y)

    def predict_proba(self, features: np.ndarray) -> float:
        if self.constant_probability is not None:
            return self.constant_probability
        if self.model is None:
            return 0.5
        if not np.isfinite(features).all():
            return 0.5
        probs = self.model.predict_proba([features])[0]
        return float(probs[1])
