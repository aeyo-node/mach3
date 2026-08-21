# Troubleshooting & FAQs

This document details resolutions for typical production issues in Swaram Market Engine.

---

## 1. Redis Cache Empty or Missing Snapshots
- **Problem**: REST endpoints `/market/{symbol}` return `waiting` or empty fallbacks.
- **Solution**: Check if ingestion collectors are running:
  ```bash
  docker-compose logs collector-delta
  docker-compose logs collector-multi
  ```
  Ensure Redis container is healthy:
  ```bash
  docker-compose ps redis
  ```

---

## 2. Delta Websocket Reconnection Loops
- **Problem**: Delta ingestion collector loops on WebSocket errors.
- **Solution**: Confirm connection endpoint internet availability. Delta Testnet WS may be down or rate-limiting. Check fallback Rest API functionality.

---

## 3. Database Migration Out of Sync
- **Problem**: Startup crashes due to missing tables or column mismatch.
- **Solution**: Run migration upgrades manually:
  ```bash
  docker-compose run --entrypoint "poetry run alembic upgrade head" api
  ```
