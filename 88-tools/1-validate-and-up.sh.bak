#!/bin/bash
# 1-validate-and-up.sh - Validate and launch stack
# Version: 0.2.0 - 2025-07-15 23:40 UTC
# Changelog:
# - Removed legacy CADDY_* port checks
# - Ensures 'charliehub_net' exists if marked external

cd "$(dirname "$0")"

echo "🚀 Step 1: Running environment check..."
./check-env.sh
if [ $? -ne 0 ]; then
  echo "❌ Environment validation failed. Aborting launch."
  exit 1
fi

echo "🔌 Step 2: Ensuring Docker network 'charliehub_net' exists..."
if ! docker network ls --format '{{.Name}}' | grep -q "^charliehub_net$"; then
  docker network create --driver bridge charliehub_net
  echo "✅ Created missing network: charliehub_net"
else
  echo "✅ Network 'charliehub_net' already exists"
fi

echo "✅ Environment valid. Proceeding with Docker Compose build & up..."
cd ..
docker compose -f docker-compose.yml --env-file .env up -d --build