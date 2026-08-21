# Database & Time-Series Storage Schema

## 1. Relational Tables
* `instruments`: Master table for tradable products, mapping canonical identifiers (`CRYPTO:BTC/USD`) to exchange-specific provider symbols (`BTCUSD`), with tick and lot sizing specifications.

## 2. TimescaleDB Hypertables
* `ticks`: Fine-grained bid, ask, mid, last prices and sizes with source vs ingestion timestamps.
* `trades`: Executed trade stream with side, size, and trade identifier.
* `candles`: Standardized OHLCV candlesticks across timeframes (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`).
* `orderbook_snapshots`: Periodic depth snapshots containing computed `best_bid`, `best_ask`, `spread`, `bid_depth`, `ask_depth`, `imbalance`, and `microprice`.
* `funding`: Perpetual contract funding rates and next settlement realization timestamps.
* `open_interest`: Open contracts and notional value.
* `provider_health_records`: Telemetry log tracking provider statuses, latency, message rates, and error logs over time.
