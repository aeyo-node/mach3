#!/bin/bash
# Swaram Market Engine - EC2 Setup & Run Script
# Run this once after cloning the repo on Ubuntu EC2
# Usage: bash scripts/ec2_setup.sh

set -e
echo "=== Swaram Market Engine: EC2 Setup ==="

# ---- 1. Install Docker ----
if ! command -v docker &>/dev/null; then
    echo "[1/5] Installing Docker..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release

    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Allow current user to run docker without sudo
    sudo usermod -aG docker $USER
    echo "[1/5] Docker installed. NOTE: Run 'newgrp docker' or logout/login if you get permission errors."
else
    echo "[1/5] Docker already installed: $(docker --version)"
fi

# ---- 2. Verify Docker Compose ----
if ! docker compose version &>/dev/null; then
    echo "[2/5] Installing docker-compose-plugin..."
    sudo apt-get install -y docker-compose-plugin
else
    echo "[2/5] Docker Compose: $(docker compose version)"
fi

# ---- 3. Create .env from example ----
if [ ! -f .env ]; then
    echo "[3/5] Creating .env from .env.example..."
    cp .env.example .env
    echo "[3/5] .env created. EDIT IT NOW before starting:"
    echo "      nano .env"
    echo ""
    echo "  Required fields to set:"
    echo "    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB"
    echo "    DATABASE_URL (uses same credentials)"
    echo ""
else
    echo "[3/5] .env already exists, skipping."
fi

# ---- 4. Build & Start ----
echo "[4/5] Building Docker images..."
sudo docker compose build --no-cache

echo "[5/5] Starting services..."
sudo docker compose up -d

echo ""
echo "=== Setup Complete ==="
echo "Services starting. Check status with:"
echo "  docker compose ps"
echo "  docker compose logs -f"
echo ""
echo "Health check (wait ~30 seconds for DB init):"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/health/providers"
echo "  curl http://localhost:8000/market/BTCUSD"
