#!/bin/bash
# Swaram Market Engine - Pull latest code and restart services
# Usage: bash scripts/redeploy.sh

set -e
echo "=== Swaram: Redeploying ==="

git pull origin main

docker compose down
docker compose build --no-cache
docker compose up -d

echo "Redeployment complete."
docker compose ps
