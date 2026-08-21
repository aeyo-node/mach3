#!/bin/bash
# Swaram Market Engine - Clean Docker cache/volumes and redeploy
# Usage: bash scripts/clean_and_redeploy.sh

set -e
echo "=== Swaram: Cleaning Docker cache & redeploying ==="

# 1. Pull latest code from git
git pull origin main

# 2. Stop running containers
echo "Stopping containers..."
docker compose down --volumes --remove-orphans || true

# 3. Clean unused Docker cache, images, and volumes
echo "Pruning unused docker containers, images, build cache, and volumes..."
docker system prune -af --volumes

# 4. Rebuild from scratch and start
echo "Rebuilding and starting services..."
docker compose up -d --build

echo "=== Deployment Complete ==="
docker compose ps
