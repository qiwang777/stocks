from __future__ import annotations

import asyncio
from datetime import datetime, time, timedelta, timezone
from typing import Iterable

from stock_predictor.services.prediction import PredictionService


class RetrainingScheduler:
    def __init__(
        self,
        prediction_service: PredictionService,
        symbols: Iterable[str] = ("AAPL", "MSFT", "NVDA", "SPY"),
        run_at: time = time(hour=8, minute=5, tzinfo=timezone.utc),
        enabled: bool = True,
    ):
        self.prediction_service = prediction_service
        self.symbols = tuple(symbol.strip().upper() for symbol in symbols if symbol.strip())
        self.run_at = run_at
        self.enabled = enabled
        self._task: asyncio.Task[None] | None = None
        self.last_results: dict[str, str] = {}

    def retrain(self) -> dict[str, str]:
        self.last_results = self.prediction_service.retrain(list(self.symbols))
        return self.last_results

    async def start(self) -> None:
        if not self.enabled or self._task is not None:
            return
        self._task = asyncio.create_task(self._run_loop(), name="model-retrain-scheduler")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run_loop(self) -> None:
        while True:
            await asyncio.sleep(self._seconds_until_next_run())
            await asyncio.to_thread(self.retrain)

    def _seconds_until_next_run(self) -> float:
        now = datetime.now(timezone.utc)
        target = datetime.combine(now.date(), self.run_at, tzinfo=timezone.utc)
        if target <= now:
            target += timedelta(days=1)
        return max(0.0, (target - now).total_seconds())
