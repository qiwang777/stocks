# PredictStockPrice — Stock Prediction Service (Spring Boot)

<img width="1917" height="1017" alt="image" src="https://github.com/user-attachments/assets/ba24993e-1559-4e58-826f-e5262985dc55" />


[![Maven Build](https://img.shields.io/badge/build-maven-blue)](https://maven.apache.org/)

**Title**: PredictStockPrice — Stock Prediction Service

**Objective**: Provide short-term stock movement predictions (direction + confidence) with optional LLM-style rationales, exposed via REST and streaming APIs.

**Quick Overview**
- **API base**: `/api/v1`
- **Prediction**: `POST /api/v1/predict` — request body: `PredictionRequest` (JSON) — returns a `Prediction` (symbol, horizon, asOf, lastPrice, predictedMove, confidence, rationale).
- **History**: `GET /api/v1/history?symbol=SYMBOL&range=3mo` — returns historical bars in `HistoryResponse`.
- **Streaming quotes (SSE)**: `GET /api/v1/stream/quotes?symbol=SYMBOL` — Server-Sent Events (text/event-stream) emitting price ticks.

**Project Structure (key files)**
- `src/main/java/com/PredictStockPrice/stocks/web/PredictionController.java` — prediction REST endpoint.
- `src/main/java/com/PredictStockPrice/stocks/web/HistoryController.java` — historical data endpoint.
- `src/main/java/com/PredictStockPrice/stocks/web/StreamController.java` — SSE price stream.
- `src/main/java/com/PredictStockPrice/stocks/service/PredictionService.java` — core prediction logic.
- `src/main/java/com/PredictStockPrice/stocks/ml/FeatureEngineering.java` and `ml/SmileModel.java` — feature extraction and ML model usage.
- `src/main/java/com/PredictStockPrice/stocks/data/MarketDataClient.java` — market data ingestion and streaming.
- `src/main/java/com/PredictStockPrice/stocks/model/Prediction.java` — prediction DTO (includes optional `rationale`).

**Build & Run (Windows PowerShell)**
```powershell
.\mvnw.cmd package
.\mvnw.cmd spring-boot:run
# or, after package:
java -jar target\*.jar
```

**Example Requests**
- Predict (JSON body):
```bash
curl -X POST http://localhost:8080/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","horizon":"1d"}'
```
- History:
```bash
curl "http://localhost:8080/api/v1/history?symbol=AAPL&range=3mo"
```
- SSE stream (watch live ticks):
```bash
curl "http://localhost:8080/api/v1/stream/quotes?symbol=AAPL"
```

**Configuration**
- Application properties live in `src/main/resources/application.yml` and `application.properties` (see `WebClientConfig` and `SpringAiConfig` for external service hooks).

**Value Proposition**
- Demonstrates an end-to-end ML-enabled backend: data ingestion, feature engineering, model integration, scheduled retraining, REST + streaming interfaces, and optional explainability via `rationale` text.

**Next steps / Suggestions**
- Add README sections for deployment (Docker, Kubernetes) and environment variables.
- Document `PredictionRequest` and `HistoryResponse` DTO shapes for easier API clients.
- Add sample curl/Postman collection and a minimal front-end to demo the SSE stream.

**DTO Examples**

- `PredictionRequest` (request to `/api/v1/predict`):

```json
{
  "symbol": "AAPL",
  "horizon": "1d"
}
```

- `HistoryResponse` (example structure returned from `/api/v1/history`):

```json
{
  "symbol": "AAPL",
  "interval": "1d",
  "bars": [
    { "time": "2025-11-14T00:00:00Z", "open": 174.0, "high": 176.0, "low": 172.5, "close": 175.2, "volume": 1200000 },
    { "time": "2025-11-13T00:00:00Z", "open": 172.5, "high": 174.1, "low": 171.8, "close": 173.6, "volume": 980000 }
  ]
}
```

- `Prediction` (response from `/api/v1/predict`):

```json
{
  "symbol": "AAPL",
  "horizon": "1d",
  "asOf": "2025-11-16T12:34:56Z",
  "lastPrice": 175.20,
  "predictedMove": "UP",
  "confidence": 0.72,
  "rationale": "Momentum indicators and recent volume spike suggest short-term upside."
}
```

---
Generated from the project source in this repository.
