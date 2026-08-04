from typing import Optional
import numpy as np
from sklearn.linear_model import LogisticRegression

class SmileModel:
    def __init__(self):
        self.model: Optional[LogisticRegression] = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        if X.size == 0:
            self.model = None
            return
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X, y)

    def predict_proba(self, features: np.ndarray) -> float:
        if self.model is None:
            return 0.5
        probs = self.model.predict_proba([features])[0]
        return float(probs[1])
