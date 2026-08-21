# Deployment Guide

This guide explains how to deploy, manage, and scale the Swaram Market Engine.

---

## 1. Requirements

- Docker Engine 20.10+
- Docker Compose v2.0+
- At least 2 Cores, 4GB RAM (e.g., AWS EC2 `t3.medium` or larger)
- Exposed Ports:
  - `8000` (FastAPI REST & WebSocket API)
  - `9090` (Prometheus Metrics Scraper)

---

## 2. Fast Deploy on EC2

To perform a clean build and redeployment:

```bash
cd ~/mach3
bash scripts/clean_and_redeploy.sh
```

This script:
1. Stops and removes existing containers.
2. Prunes unused volumes and caches to reclaim disk space.
3. Performs a clean build of the API and Collector images.
4. Launches the PostgreSQL/TimescaleDB, Redis, API Server, and Ingestion Collectors.

---

## 3. Verifying the Deployment

### Health Check
```bash
curl http://localhost:8000/health
```

### Market Ticker
```bash
curl http://localhost:8000/market/BTCUSD
```

### Metrics Scraper
```bash
curl http://localhost:8000/metrics
```
