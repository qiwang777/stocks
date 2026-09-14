# Market Data Providers

All six providers implement the same daily-history and latest-price operations.
History, prediction and SSE accept an optional `datasource` query parameter.
Omitting it uses the default from `.env`. There is no automatic fallback between
providers, and selecting a source for one request does not change other requests.

## Per-Request Selection

```text
GET /api/v1/history?symbol=AAPL&range=3mo&datasource=yfinance
POST /api/v1/predict?datasource=fmp
GET /api/v1/stream/quotes?symbol=AAPL&datasource=massive
```

The POST body remains `{"symbol":"AAPL","horizon":"1d"}`; `datasource` goes in
the query string for all endpoints. Values are case-insensitive and displayed as
an enum in the interactive API docs. Unknown or blank values return HTTP 422.

Each provider owns separate history caches, HTTP clients and prediction models.
Simultaneous requests for the same ticker from different providers do not share
training data or models. Daily scheduled retraining continues to target the default
provider; other sources train on demand. All provider HTTP clients close at shutdown.

History and prediction JSON report `"dataSource": ["yfinance"]` when that source
supplied the historical bars, including short histories. Empty histories produce
`"dataSource": []`, not a claim that usable data was obtained. SSE reports the
selected source in `X-Data-Source: yfinance` while retaining `data: 123.45` messages.
The header identifies the stream provider even when it currently has no prices.

## Configuration

To change the default, edit `.env` in the repository root and restart the service:

```dotenv
MARKETDATA_PROVIDER=yfinance
```

The provider names are case-insensitive. All API-key slots in the local `.env`
are blank for you to fill in; yfinance has no API-key setting.

| Provider value | Credential field | Example symbol |
| --- | --- | --- |
| `alphavantage` | `MARKETDATA_AV_KEY` | `AAPL` |
| `finage` | `MARKETDATA_FINAGE_KEY` | `AAPL` |
| `yfinance` | None | `AAPL`, `VOD.L` |
| `eodhd` | `MARKETDATA_EODHD_KEY` | `AAPL` becomes `AAPL.US`; `VOD.LSE` stays unchanged |
| `massive` | `MARKETDATA_MASSIVE_KEY` | `AAPL` |
| `fmp` | `MARKETDATA_FMP_KEY` | `AAPL` |

For example, to use EODHD, fill in `MARKETDATA_EODHD_KEY` and choose either
`MARKETDATA_PROVIDER=eodhd` or `?datasource=eodhd`. Base URLs are preconfigured in `.env` and `.env.example`.
Start from the repository root so the `.env` is loaded. Process environment
variables override `.env`. Changing settings requires a restart, which also clears
in-memory caches and models.

REST providers with blank keys return empty history/no quote without making a
request. History fetch failures, invalid rows and invalid prices are handled without
using another provider's data. Failed/empty histories are not cached.

## Provider Implementations

- Alpha Vantage keeps the existing `TIME_SERIES_DAILY` compact history and
  `GLOBAL_QUOTE` endpoints.
- Finage keeps daily stock aggregates and `/last/stock/{symbol}`.
- Yahoo Finance uses `Ticker.history(interval="1d", auto_adjust=False)` and
  `fast_info["last_price"]`. The SDK call for an async quote runs in a worker thread.
  See the [yfinance Ticker documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html).
- EODHD uses `/eod/{symbol}` and `/real-time/{symbol}`, with `api_token` authentication.
  See [historical data](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes)
  and [delayed quotes](https://eodhd.com/financial-apis/live-ohlcv-stocks-api).
- Massive uses `/v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}` and
  `/v2/last/trade/{symbol}`, with `apiKey` authentication. Historical pagination is
  followed only on the configured provider origin. A failed later page invalidates
  the download rather than caching a partial result. See [custom bars](https://massive.com/docs/rest/stocks/aggregates/custom-bars)
  and [last trade](https://massive.com/docs/rest/stocks/trades-quotes/last-trade).
- FMP uses the stable `/historical-price-eod/full` and `/quote` endpoints with
  `symbol` and `apikey` query parameters. See [daily history](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full)
  and [quotes](https://site.financialmodelingprep.com/developer/docs/stable/quote/).

## Data And Polling Semantics

History is converted to `HistoryResponse` / `Bar`, sorted by ascending UTC timestamp
and deduplicated by timestamp. Daily date strings without a timezone are interpreted
as UTC; exchange-local timestamps from Yahoo retain their instant when converted
to UTC. Non-finite OHLC values, invalid dates and invalid volumes are skipped.

The existing numeric ranges (`1d`, `1wk`, `3mo`, `1y`) use approximate calendar
windows: a month is 30 days and a year is 365 days. Yahoo's exclusive end date is
advanced by one day. Alpha Vantage retains its existing compact-history behavior
and ignores the range. `max` and `ytd` are not supported range modes.

Adapters use provider-native OHLC fields, never an adjusted close substituted into
an otherwise unchanged OHLC row. Yahoo explicitly disables automatic adjustment;
Massive requests `adjusted=false`. This does not establish identical corporate-action
adjustments or daily-session boundaries across vendors. Use one consistent data
source for a training/backtest dataset.

The SSE endpoint is polling, not a guaranteed real-time exchange feed. EODHD's REST
quote is delayed; Massive's last-trade access depends on the subscription. See their
linked endpoint documentation above. Increase `MARKETDATA_POLL_SECONDS` to fit your
request allowance. Each connected stream polls independently. No previous-close
fallback is presented as a live trade.

## Verification

Tests use mocked REST responses and mocked yfinance tickers. They check request
URLs/authentication, date windows, history conversion and caching, quote polling,
blank keys, upstream errors, pagination, timezone handling, worker-thread execution,
and API-to-model integration. No paid-provider requests or live credential checks
are made by the test suite.
