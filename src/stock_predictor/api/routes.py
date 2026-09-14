from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from stock_predictor.api.dependencies import get_market_data, get_prediction_service
from stock_predictor.data.market_data import MarketDataClient
from stock_predictor.schemas import HistoryResponse, Prediction, PredictionRequest
from stock_predictor.services.prediction import PredictionService

router = APIRouter(prefix="/api/v1")


@router.get("/history", response_model=HistoryResponse)
def history(
    symbol: str = Query(..., min_length=1, pattern=r"\S"),
    range: str = Query("3mo", min_length=1, pattern=r"\S"),
    market_data: MarketDataClient = Depends(get_market_data),
):
    return market_data.get_daily_history(symbol, range)


@router.post("/predict", response_model=Prediction, response_model_by_alias=True)
def predict(
    request: PredictionRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    return service.predict(request.symbol, request.horizon)


@router.get("/stream/quotes")
def stream_quotes(
    request: Request,
    symbol: str = Query(..., min_length=1, pattern=r"\S"),
    market_data: MarketDataClient = Depends(get_market_data),
):
    async def generate():
        async for price in market_data.stream_prices_async(symbol):
            if await request.is_disconnected():
                break
            yield f"data: {price}\n\n"

    return StreamingResponse(
        generate(), media_type="text/event-stream",
        headers={"X-Data-Source": market_data.provider},
    )
