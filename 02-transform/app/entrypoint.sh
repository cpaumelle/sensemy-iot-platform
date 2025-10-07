#!/bin/bash
# entrypoint.sh - Start cron + FastAPI
# Version: 0.1.3 - 2025-07-23 15:50 UTC
# Changelog:
# - FIXED: run uvicorn main:app instead of app.main when /app is root

set -e

touch /var/log/cron.log /var/log/cron_heartbeat.log
echo "📆 Starting cron..."
service cron start

sleep 1
echo "🚀 Starting FastAPI (Uvicorn)..."

exec uvicorn main:app --host 0.0.0.0 --port 9001 --log-level debug