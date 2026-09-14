"""FastAPI assembly and application-owned resource lifecycle."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from stock_predictor.api.routes import router
from stock_predictor.core.config import Settings
from stock_predictor.data.market_data import MarketDataClient
from stock_predictor.jobs.retraining import RetrainingScheduler
from stock_predictor.services.prediction import PredictionService
from stock_predictor.services.rationale import RationaleService
from stock_predictor.schemas import DataSource


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        market_data_by_source = {
            source.value: MarketDataClient(
                settings.alpha_vantage_base_url,
                settings.alpha_vantage_api_key,
                source.value,
                finage_base=settings.finage_base_url,
                finage_key=settings.finage_api_key,
                eodhd_base=settings.eodhd_base_url,
                eodhd_key=settings.eodhd_api_key,
                massive_base=settings.massive_base_url,
                massive_key=settings.massive_api_key,
                fmp_base=settings.fmp_base_url,
                fmp_key=settings.fmp_api_key,
                quote_poll_seconds=settings.quote_poll_seconds,
                cache_ttl_seconds=settings.cache_ttl_seconds,
                cache_max_size=settings.cache_max_size,
            )
            for source in DataSource
        }
        rationale = RationaleService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            base_url=settings.openai_base_url,
        )
        services = {
            source: PredictionService(market_data, rationale)
            for source, market_data in market_data_by_source.items()
        }
        market_data = market_data_by_source[settings.market_data_provider]
        service = services[settings.market_data_provider]
        scheduler = RetrainingScheduler(
            service, symbols=settings.retraining_symbols, enabled=settings.retraining_enabled
        )
        app.state.market_data = market_data
        app.state.market_data_by_source = market_data_by_source
        app.state.rationale_service = rationale
        app.state.prediction_service = service
        app.state.prediction_services = services
        app.state.scheduler = scheduler
        try:
            await scheduler.start()
            yield
        finally:
            await scheduler.stop()
            for source_client in market_data_by_source.values():
                await source_client.aclose()
                source_client.close()
            rationale.close()

    app = FastAPI(title="Stock Predictor", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(router)
    return app


def run() -> None:
    settings = Settings.from_env()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
