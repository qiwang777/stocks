# Stock Predictor

Python 3.11+ service for stock direction predictions, historical bars and streaming
quotes. FastAPI serves the API; scikit-learn trains the logistic regression model.
The original Spring Boot project is preserved in [archive/java-stock-predictor](archive/java-stock-predictor/).

## Setup

Run from the repository root. A virtual environment is recommended:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m stock_predictor
```

With dependencies already installed, a source checkout also supports:

```powershell
python scripts/check_runtime.py
python scripts/run_server.py
```

The default address is http://127.0.0.1:8080, with interactive API documentation at
http://127.0.0.1:8080/docs. `HOST` and `PORT` override the bind address.
After installation, `stock-predictor` is also available as a console command.
For development reload:

```powershell
python -m uvicorn stock_predictor.app:create_app --factory --app-dir src --reload --port 8080
```

If the port is occupied, select another one using `PORT` or Uvicorn's `--port`.

## Configuration

Settings read environment variables and an optional `.env` in the current working
directory. Existing environment variables take precedence. See [.env.example](.env.example)
for all settings. No API keys are required to start the service or run offline tests.
The REST providers require their own credentials; yfinance does not use an API key.
AI rationales require an optional OpenAI key. Edit the local `.env`, then restart
the service to change the default provider or credentials. Each API call can
override the default with `?datasource=yfinance`. See [provider setup](docs/providers.md).

| Setting | Default |
| --- | --- |
| `HOST`, `PORT` | `127.0.0.1`, `8080` |
| `MARKETDATA_PROVIDER` | `alphaVantage`; also `finage`, `yfinance`, `eodhd`, `massive`, `fmp` |
| `MARKETDATA_AV_BASE`, `MARKETDATA_AV_KEY` | Alpha Vantage URL, empty key |
| `MARKETDATA_FINAGE_BASE`, `MARKETDATA_FINAGE_KEY` | Finage URL, empty key |
| `MARKETDATA_EODHD_BASE`, `MARKETDATA_EODHD_KEY` | `https://eodhd.com/api`, empty key |
| `MARKETDATA_MASSIVE_BASE`, `MARKETDATA_MASSIVE_KEY` | `https://api.massive.com`, empty key |
| `MARKETDATA_FMP_BASE`, `MARKETDATA_FMP_KEY` | `https://financialmodelingprep.com/stable`, empty key |
| `MARKETDATA_POLL_SECONDS` | 3 seconds; increase to match your plan's rate limit |
| `CACHE_TTL_SECONDS`, `CACHE_MAX_SIZE` | 600 seconds, 500 history entries |
| `MODEL_RETRAIN_ENABLED` | `true` |
| `MODEL_RETRAIN_SYMBOLS` | `AAPL,MSFT,NVDA,SPY` |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | empty key, `gpt-4o-mini` |
| `OPENAI_BASE_URL`, `OPENAI_TEMPERATURE` | `https://api.openai.com/v1`, `0.2` |

`FINAGE_API_KEY`, `SPRING_AI_OPENAI_API_KEY` and
`SPRING_AI_OPENAI_CHAT_OPTIONS_MODEL` remain fallback environment variable names.
Invalid settings such as a negative cache size fail during startup.

## API

| Method | Path | Input |
| --- | --- | --- |
| GET | `/api/v1/history` | `symbol=AAPL&range=3mo&datasource=yfinance` |
| POST | `/api/v1/predict?datasource=yfinance` | `{"symbol":"AAPL","horizon":"1d"}` |
| GET | `/api/v1/stream/quotes` | `symbol=AAPL&datasource=yfinance` |

Prediction JSON retains `asOf`, `lastPrice`, and `predictedMove` for existing clients.
`datasource` is optional and case-insensitive on all three endpoints. Supported
values are `alphavantage`, `finage`, `yfinance`, `eodhd`, `massive`, and `fmp`.
Unknown values return HTTP 422. History and prediction JSON include `dataSource`,
a list of contributing providers (empty when no historical bars were returned).
SSE keeps its numeric price messages and reports the selected provider in the
`X-Data-Source` response header.
Examples and the Postman collection remain in [examples](examples/).

Confidence：
0.0：几乎没有方向信心，说明模型接近 50/50
0.2：略微偏向某个方向
0.5：中等强度
1.0：非常强，说明模型几乎确定了方向

## Behavior And Limits

- Each provider has a separate bounded 10-minute history cache and prediction models.
- Predictions reuse in-memory models. Daily retraining replaces the default
  provider's models at 08:05 UTC; other providers train on demand.
- Run one server worker when using the embedded scheduler: each process owns its
  own models, cache and scheduled job. Models are lost on restart.
- SSE polls the selected provider every three seconds by default, controlled by
  `MARKETDATA_POLL_SECONDS`. Quote availability and delay depend on the provider.
- Alpha Vantage history still uses compact daily output; its `range` input does not
  filter the data. The model predicts the next daily direction; `horizon` is not yet
  a separate training target.
- Upstream failures may return empty history or an unavailable rationale. An empty
  response is not evidence of a working live data connection.
- Empty or failed historical downloads are not cached. Missing REST API keys skip
  requests; no automatic fallback to another provider occurs.
- Offline tests validate software behavior, not investment performance or provider
  access. There is no broker integration, backtest or persistent model store yet.

## Layout

```text
src/stock_predictor/   Python application package
  api/                HTTP routes and dependency accessors
  core/               Validated configuration and history cache
  data/               Market data clients and provider parsers
    providers/        Alpha Vantage, Finage, Yahoo Finance, EODHD, Massive and FMP
  ml/                 Technical features and logistic regression
  services/           Prediction and rationale workflows
  jobs/               Daily retraining lifecycle
  app.py              Application factory and resource ownership
  schemas.py          Shared bar and API data schemas
tests/                Offline tests grouped by application responsibility
scripts/              Source-checkout startup and runtime checks
docs/                 Structure and verification notes
examples/             Public API request/response examples
archive/java-stock-predictor/  Original Java project and Maven tooling
```

See [the file map](docs/structure.md) and [runtime verification](docs/runtime-status.md).
