from fastapi import Query, Request

from stock_predictor.data.market_data import MarketDataClient
from stock_predictor.services.prediction import PredictionService
from stock_predictor.schemas import DataSource


def get_market_data(
    request: Request,
    datasource: DataSource | None = Query(default=None, description="Provider for this request; defaults to MARKETDATA_PROVIDER."),
) -> MarketDataClient:
    if datasource is None:
        return request.app.state.market_data
    return request.app.state.market_data_by_source[datasource.value]


def get_prediction_service(
    request: Request,
    datasource: DataSource | None = Query(default=None, description="Provider for this request; defaults to MARKETDATA_PROVIDER."),
) -> PredictionService:
    if datasource is None:
        return request.app.state.prediction_service
    return request.app.state.prediction_services[datasource.value]
