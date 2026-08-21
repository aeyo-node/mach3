# Swaram Market Engine Architecture

## 1. System Topology

```text
┌───────────────────────────────────────────────────────────┐
│                     External Feeds                        │
│   Delta Exchange WS │ Bybit │ Deribit │ cTrader │ Macro   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                   Collectors Daemon                       │
│  - Resilient WebSocket connection (heartbeat/backoff/jitter)│
│  - Stale feed watchdog & gap detection                    │
│  - Ingestion latency metrics & health evaluation          │
│  - Canonical symbol translation                           │
└──────────────┬─────────────────────────────┬──────────────┘
               │                             │
       (Live Snapshots)               (Batch Buffer)
               ▼                             ▼
┌─────────────────────────────┐ ┌───────────────────────────┐
│           Redis 7           │ │   PostgreSQL/TimescaleDB  │
│  - market:snapshot:{symbol} │ │  - instruments (metadata) │
│  - health:provider:{name}   │ │  - ticks, trades, candles │
│  - Pub/Sub event bus        │ │  - orderbook_snapshots    │
└──────────────┬──────────────┘ └─────────────┬─────────────┘
               │                             │
               └──────────────┬──────────────┘
                              ▼
┌───────────────────────────────────────────────────────────┐
│                       FastAPI                             │
│  - GET /health                                            │
│  - GET /health/providers                                  │
│  - GET /market/{symbol}                                   │
│  - GET /market/{symbol}/candles                           │
│  - GET /market/{symbol}/orderbook                         │
└───────────────────────────────────────────────────────────┘
```

## 2. Ingestion & Quality Control
* Every raw observation computes `latency_ms = (received_at - source_timestamp)`.
* Watchdog flags feed status as `HEALTHY`, `STALE` (if no message within threshold), `DEGRADED`, or `DISCONNECTED`.
* Orderbook metrics compute top-of-book spread, basis points, 20-level bid/ask depth sums, order book imbalance, and microprice.
