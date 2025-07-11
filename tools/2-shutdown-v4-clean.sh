#!/bin/bash
# 2-shutdown-v4-clean.sh - Tear down all V4 containers
# Version: 0.1.0
# Updated: 2025-07-10 23:05 UTC

cd "$(dirname "$0")/.."

echo "🧹 Shutting down all V4 containers..."
docker compose -f docker-compose-v4.yml --env-file .env.v4 down

echo "✅ V4 stack shut down cleanly."
