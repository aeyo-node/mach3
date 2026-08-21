# Swaram Market Engine

**Swaram Market Engine** is a production-grade, multi-market quantitative intelligence platform. It continuously observes cryptocurrency, crypto derivatives, forex, precious metals, macro indicators, interest-rate expectations, and financial events, transforming raw data into deterministic machine-readable features, market structure levels, and real-time analytical feeds.

---

## Core Architecture Principles

* **LLMs reason.**
* **Python calculates.**
* **Databases remember.**
* **WebSockets observe.**
* **ML estimates probabilities.**
* **Hermes orchestrates specialist reasoning.**
* **n8n handles business and workflow automation.**

---

## Initial Phase 0 & 1 Features

* **Delta Exchange India WebSocket Pipeline**: Resilient real-time ingestion (`wss://public-socket.india.delta.exchange`) for `BTCUSD` and `ETHUSD` (L1 quotes, trades, 1m candlesticks, L2 orderbook with imbalance and microprice, mark/spot prices, and funding rates).
* **Dual-Tier State Architecture**:
  * **Redis 7**: Sub-millisecond live market snapshots, orderbook depth metrics, and real-time provider health telemetry.
  * **PostgreSQL / TimescaleDB**: Durable time-series hypertables with automated batch buffering for ticks, trades, candles, and orderbook snapshots.
* **Strict UTC & Asia/Kolkata Formatting**: All internal storage, comparisons, and timestamps are timezone-aware UTC, with seamless user-facing conversions to `Asia/Kolkata` (IST).
* **FastAPI Service**: High-performance REST endpoints for health telemetry (`/health`, `/health/providers`) and market snapshots (`/market/{symbol}`, `/market/{symbol}/candles`, `/market/{symbol}/orderbook`).
* **Canonical Symbol System**: Automatically translates venue-specific tickers (e.g. `BTCUSD`, `BTCUSDT`, `BTC-PERPETUAL`) into unified identifiers (e.g. `CRYPTO:BTC/USD`, `FX:EUR/USD`, `METAL:XAU/USD`).

---

## Quickstart

### 1. Requirements
* Docker & Docker Compose
* Python 3.11+ (for local development)

### 2. Environment Setup
```bash
cp .env.example .env
```

### 3. Launch via Docker Compose
```bash
docker compose up -d --build
```

### 4. Verify System Health & Live Market Ingestion
```bash
# Check service health
curl http://localhost:8000/health

# Check provider connection status & latency
curl http://localhost:8000/health/providers

# Get live BTC market snapshot
curl http://localhost:8000/market/BTCUSD
```

---

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v
```
