# Binance Futures Testnet Trading Bot

A small, structured Python CLI for placing MARKET, LIMIT, and STOP_LIMIT orders on
**Binance Futures Testnet (USDT-M)**, with input validation, error handling, and
request/response logging.

## Project structure

```
trading_bot/
  bot/
    __init__.py
    client.py           # Signed REST client for Binance Futures (requests-based)
    orders.py           # Translates MARKET/LIMIT/STOP_LIMIT into API calls
    validators.py        # CLI input validation (no network calls)
    logging_config.py    # Rotating file logger + console handler
  cli.py                 # argparse CLI entry point
  tests/
    test_validators.py   # Unit tests for validation logic
  logs/                   # Created at runtime; trading_bot.log lives here
  requirements.txt
  .env.example
  README.md
```

- **client.py** only knows how to talk to the Binance REST API (signing, HTTP, error
  wrapping). It has no knowledge of MARKET vs LIMIT semantics.
- **orders.py** is the "business logic" layer: it knows how to turn a
  MARKET/LIMIT/STOP_LIMIT request into the right API parameters.
- **cli.py** is the presentation layer: argument parsing, printing the summary and
  result, and mapping exceptions to exit codes.

This split means `bot/` could back a different frontend (web API, Telegram bot, etc.)
without changes.

## Setup

1. **Create a Binance Futures Testnet account** at https://testnet.binancefuture.com
   and generate an API key + secret from the testnet dashboard.

2. **Clone/copy this project**, then install dependencies (Python 3.9+):

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials.** Copy `.env.example` to `.env` and fill in your keys,
   then export them (this project reads plain environment variables — add
   `python-dotenv` yourself if you'd rather auto-load a `.env` file):

   ```bash
   export BINANCE_API_KEY="your_testnet_api_key"
   export BINANCE_API_SECRET="your_testnet_api_secret"
   ```

4. Make sure your testnet account has some virtual USDT (the testnet UI has a
   "Faucet" to top up test funds) and that the symbol you trade (e.g. `BTCUSDT`)
   is enabled for futures trading on testnet.

## Usage

```bash
# Market order
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Limit order
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000

# Bonus: stop-limit order
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 \
    --price 58000 --stop-price 58500
```

Sample output:

```
Order request summary:
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.01

Order response:
  orderId     : 123456789
  status      : FILLED
  executedQty : 0.01
  avgPrice    : 60123.40

✅ Order placed successfully.
```

On failure (bad input, rejected order, or network issue), the CLI prints a labeled
error (`[INPUT ERROR]`, `[API ERROR]`, or `[UNEXPECTED ERROR]`) and exits with a
non-zero status code; full detail goes to the log file either way.

### Running tests

```bash
pip install pytest
pytest tests/ -v
```

## Logging

Every API request and response (with the API key/signature stripped out) is logged
to `logs/trading_bot.log`, along with validation failures and unexpected exceptions.
The console only shows warnings/errors, so normal CLI output stays clean while the
log file keeps the full audit trail. The log rotates at ~2MB with 3 backups kept.

> **Note on the log-file deliverable:** this repo ships the code, not fabricated
> log output — the log file only contains real content once you run the CLI
> against your own testnet credentials, since real orders need a live signed
> session against Binance's testnet servers. Run one MARKET and one LIMIT order
> (commands above) and `logs/trading_bot.log` will contain both.

## Assumptions

- Only USDT-M futures (the `/fapi/v1/...` endpoints) are in scope, not COIN-M or spot.
- `STOP_LIMIT` (the bonus order type) is implemented as Binance's `STOP` order type
  with both `price` and `stopPrice` set — Binance futures has no order type literally
  named `STOP_LIMIT`.
- LIMIT and STOP_LIMIT orders default to `GTC` (Good-Til-Cancelled) time-in-force,
  since the task didn't require exposing that as a CLI flag.
- Quantity/price precision (tick size, step size, min notional) is validated by
  Binance itself; this bot does basic type/positivity checks but does not fetch and
  enforce exchange filters, to keep the scope of the "simplified" bot reasonable.
- Credentials are read from environment variables rather than a config file or CLI
  flags, so they're never printed or logged.
