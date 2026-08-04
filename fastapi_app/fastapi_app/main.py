from fastapi import FastAPI, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi_app.data.market_data_client import MarketDataClient
from fastapi_app.services.prediction_service import PredictionService
from fastapi_app.rationale_service import RationaleService
from fastapi_app.models import PredictionRequest, Prediction, HistoryResponse
import os
import asyncio
import uvicorn

app = FastAPI(title="stocks-fastapi")

# Config from env or defaults
AV_BASE = os.environ.get("MARKETDATA_AV_BASE", "https://www.alphavantage.co")
AV_KEY = os.environ.get("MARKETDATA_AV_KEY", "")
PROVIDER = os.environ.get("MARKETDATA_PROVIDER", "alphaVantage")

market_client = MarketDataClient(AV_BASE, AV_KEY, PROVIDER)
rationale = RationaleService()
pred_service = PredictionService(market_client, rationale)

@app.get("/api/v1/history", response_model=HistoryResponse)
def history(symbol: str, range: str = "3mo"):
    return market_client.get_daily_history(symbol, range)

@app.post("/api/v1/predict", response_model=Prediction)
def predict(req: PredictionRequest):
    return pred_service.predict(req.symbol, req.horizon)

@app.get("/api/v1/stream/quotes")
def stream_quotes(symbol: str):
    async def generator():
        for price in market_client.stream_prices(symbol):
            yield f"data: {price}\n\n"
            await asyncio.sleep(0)
    return StreamingResponse(generator(), media_type="text/event-stream")


def run():
    uvicorn.run("fastapi_app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), reload=False)

if __name__ == "__main__":
    run()
