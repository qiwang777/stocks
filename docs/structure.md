# Project Structure

The repository root is the active Python project. `stock_predictor` names the
business domain independently of the HTTP framework. Modules use snake_case.
Folders group related responsibilities; filenames omit redundant folder names.

| File | Responsibility |
| --- | --- |
| `src/stock_predictor/__init__.py` | Package identity; no startup side effects |
| `src/stock_predictor/__main__.py` | `python -m stock_predictor` entry point |
| `src/stock_predictor/app.py` | FastAPI factory, startup/shutdown, service wiring |
| `src/stock_predictor/schemas.py` | Bar, request and response data schemas |
| `src/stock_predictor/api/routes.py` | History, prediction and SSE endpoints |
| `src/stock_predictor/api/dependencies.py` | Request-scoped access to app-owned services |
| `src/stock_predictor/core/config.py` | Environment settings and validation |
| `src/stock_predictor/core/cache.py` | Bounded TTL history cache |
| `src/stock_predictor/data/market_data.py` | Provider selection, shared HTTP clients, caching and polling |
| `src/stock_predictor/data/providers/base.py` | Provider interface and common REST request handling |
| `src/stock_predictor/data/providers/common.py` | Date windows, UTC conversion and bar/price validation |
| `src/stock_predictor/data/providers/alpha_vantage.py` | Alpha Vantage daily bars and global quotes |
| `src/stock_predictor/data/providers/finage.py` | Finage aggregates and stock quotes |
| `src/stock_predictor/data/providers/yahoo_finance.py` | yfinance daily history and last price |
| `src/stock_predictor/data/providers/eodhd.py` | EODHD daily bars and delayed quotes |
| `src/stock_predictor/data/providers/massive.py` | Massive daily aggregates, pagination and last trades |
| `src/stock_predictor/data/providers/fmp.py` | FMP stable daily history and quotes |
| `src/stock_predictor/ml/features.py` | Returns, moving averages, RSI, volatility and labels |
| `src/stock_predictor/ml/logistic_model.py` | scikit-learn `DirectionModel` classifier |
| `src/stock_predictor/services/prediction.py` | Train, reuse models, predict, and retrain symbols |
| `src/stock_predictor/services/rationale.py` | Optional AI rationale and fallback |
| `src/stock_predictor/jobs/retraining.py` | `RetrainingScheduler`, daily 08:05 UTC |
| `scripts/run_server.py` | Start directly from the source checkout |
| `scripts/check_runtime.py` | Import every module, fit a real model, check API lifecycle |
| `tests/conftest.py` | Isolated app and deterministic historical bars |
| `tests/test_api.py` | HTTP contracts, full prediction workflow, SSE and lifecycle |
| `tests/test_datasource.py` | Per-request selection, response provenance, concurrent provider isolation and cleanup |
| `tests/test_market_data.py` | Provider parsing, caching, async quotes and failures |
| `tests/test_providers.py` | New providers, blank credentials, pagination and full prediction wiring |
| `tests/test_logistic_model.py` | Empty, one-class and real two-class model training |
| `tests/test_prediction.py` | Short history, model reuse and retraining |
| `tests/test_retraining.py` | Daily run time and default symbols |
| `tests/test_cache.py` | Expiration and capacity |
| `tests/test_rationale.py` | Optional credentials, response parsing and fallback |
| `tests/test_config.py` | Environment parsing and invalid settings |
| `pyproject.toml` | Package, runtime/test dependencies, CLI and pytest settings |
| `requirements.txt` | Compatibility entry pointing to the root Python package |

Each application subpackage has an `__init__.py` describing its responsibility.
`schemas.py` holds data objects; trained estimators live under `ml/`. This avoids
using the name `models` for two unrelated concepts.

## Renamed Python Modules

Paths in the left column are relative to the former `fastapi_app/src/fastapi_app/`.

| Previous | Current (under `src/stock_predictor/`) |
| --- | --- |
| `main.py` | `app.py`, `core/config.py`, `api/routes.py`, `api/dependencies.py` |
| `models.py` | `schemas.py` |
| `cache.py` | `core/cache.py` |
| `data/market_data_client.py` | `data/market_data.py` |
| `ml/feature_engineering.py` | `ml/features.py` |
| `ml/smile_model.py` / `SmileModel` | `ml/logistic_model.py` / `DirectionModel` |
| `services/prediction_service.py` | `services/prediction.py` |
| `rationale_service.py` | `services/rationale.py` |
| `scheduler.py` / `ModelScheduler` | `jobs/retraining.py` / `RetrainingScheduler` |

Old Python import paths and launch commands are replaced by those in the root
README. Public API URLs and successful response field names are preserved.
The mixed migration test file is split into tests named for the behaviors they cover.

## Java Archive

`archive/java-stock-predictor/` contains all 18 original Java source files, resources,
`pom.xml`, Maven wrappers, the original README and license, existing build outputs,
and local Java editor/upgrade tooling. Java package names stay unchanged so their
source paths still match the original Maven project. No Java source belongs to the
active Python package or its distribution. Root `examples/` remains shared API material.

Generated Python leftovers from the previous layout are retained under the ignored
`.cache/legacy-python/` folder. They are not source code or part of the build.
