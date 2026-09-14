# Python Runtime Verification

Verified on 2026-09-14 on Windows with Python 3.13. Tests use deterministic input
and mocked provider responses; no live market-data or AI calls were made.

## Result

The Python service can now be imported, installed, started and exercised locally.
The previous layout failed pytest collection with `ModuleNotFoundError`. The active
source package is now `src/stock_predictor`, with one root packaging/test configuration.

| Check | Result |
| --- | --- |
| Original tests, with a temporary import-path correction | 6 passed before reorganization |
| Original reorganized suite, source environment | 29 passed before provider expansion |
| Current suite, installed local virtual environment | 85 passed after provider expansion |
| Runtime checker | 28 modules imported; actual two-class fit/predict passed |
| Application lifecycle | Startup, isolated service instances and scheduler shutdown passed |
| Prediction flow | Mocked HTTP history -> features -> real scikit-learn model -> HTTP prediction passed |
| Historical data | Alpha Vantage, Finage, yfinance, EODHD, Massive and FMP parsing and caching passed |
| New providers | Blank keys, malformed payloads, auth/rate-limit failures, pagination and quote handling passed |
| yfinance | DataFrame conversion, timezone normalization and async worker-thread execution passed |
| SSE | Response framing and provider async polling passed with simulated data |
| Rationale | Simulated success, failure fallback and explicitly disabled credentials passed |
| Retraining | Default symbols, error isolation and next 08:05 UTC calculation passed |
| Source launch | `python scripts/run_server.py` served OpenAPI and docs over localhost HTTP |
| Installed module launch | `python -m stock_predictor` served HTTP from outside the repository root |
| Installed console launch | `stock-predictor` served HTTP from outside the repository root |
| Editable install | Local installation succeeded with no dependency downloads |
| Previous wheel (before provider expansion) | Built successfully; Python package and distribution metadata only |
| Bytecode compilation | All source, test and script files compiled |
| Java archive | All 18 Java source files matched their pre-move SHA-256 hashes |

The local `.venv` was created with `--system-site-packages` to reuse available
dependencies and verify packaging without downloads. This is not a clean-room
dependency install. Versions used included FastAPI 0.115.12, Pydantic 2.11.5,
httpx 0.28.1, NumPy 2.2.5, scikit-learn 1.9.0 and yfinance 0.2.63.
Standalone smoke-test server processes were stopped after verification.

## Reproduce

From the repository root after installing the test extra:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_runtime.py
.\.venv\Scripts\python.exe -m compileall -q src tests scripts
.\.venv\Scripts\python.exe -m stock_predictor
```

Open http://127.0.0.1:8080/docs after starting the server.

## Not Established By These Checks

- Live API credentials, account entitlements, rate limits or returned market data.
- Model quality, backtest returns, or numerical equivalence to Java Smile.
- A full day of scheduled operation, sustained SSE load, or multiple workers.
- A fresh dependency download/install, or execution on every supported Python version.
- Java compilation or startup. The Java project was archived without changing its source.

Models still live only in memory. The current data client can turn provider errors
into empty history, and retraining does not yet enforce a minimum data quality
threshold before replacing a model. These behaviors need attention before relying
on the service for unattended trading. The model's target remains next-day direction
regardless of the request's `horizon` value.
