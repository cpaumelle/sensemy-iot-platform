#!/bin/bash
# 1-validate-and-up.sh - Validate and launch V4 stack
# Version: 0.1.0
# Updated: 2025-07-10 23:05 UTC

cd "$(dirname "$0")"

echo "🚀 Step 1: Running environment check..."
./check-env-v4.sh
if [ $? -ne 0 ]; then
  echo "❌ Environment validation failed. Aborting launch."
  exit 1
fi

echo "✅ Environment valid. Proceeding with Docker Compose build & up..."
cd ..
docker compose -f docker-compose-v4.yml --env-file .env.v4 up -d --build
