FastAPI port of the Stocks prediction Spring Boot project.

Run (recommended inside a venv):

pip install -r requirements.txt
python -m fastapi_app.main

Configuration via env:
- MARKETDATA_AV_BASE (default https://www.alphavantage.co)
- MARKETDATA_AV_KEY
- MARKETDATA_PROVIDER (alphaVantage or finage)

Endpoints:
- GET /api/v1/history?symbol=XXX
- POST /api/v1/predict  (JSON {"symbol":"AAPL","horizon":"1d"})
- GET /api/v1/stream/quotes?symbol=XXX  (SSE polling)
