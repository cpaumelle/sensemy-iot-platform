#!/bin/bash
# 2-shutdown-clean.sh - Tear down all containers
# Version: 0.1.1
# Updated: 2025-07-12 UTC

cd "$(dirname "$0")/.."

echo "🧹 Shutting down all containers..."
docker compose -f docker-compose.yml --env-file .env down

echo "✅ Stack shut down cleanly."
