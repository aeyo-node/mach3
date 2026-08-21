# API Sources & Endpoints Documentation

## 1. Delta Exchange India Public Feeds
* **WebSocket Endpoint**: `wss://public-socket.india.delta.exchange`
* **REST Base URL**: `https://cdn.india.delta.exchange`
* **Active Channels**:
  * `v2/ticker`: 1-second top of book quotes, 24h close/high/low/volume, mark price, spot price, funding rates.
  * `all_trades`: Real-time trade executions with buyer/seller role (taker/maker).
  * `candlestick_1m`: 1-minute OHLCV candles with trade counts.
  * `l2_orderbook`: Level-2 order book depth (bid/ask ladders).
  * `mark_price` & `spot_price`: Index and mark pricing streams.

## 2. Authentication & Secrets
* No API keys or private credentials are required for public WebSocket and REST market-data ingestion.
