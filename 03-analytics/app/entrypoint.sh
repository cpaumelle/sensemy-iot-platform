#!/bin/bash
# entrypoint.sh - analytics service
# Version: 1.1.0 - 2025-08-26 22:30:00 UTC
# Added cron job loading for persistent materialized view refresh

set -e

echo "Starting SenseMy Analytics Service..."
echo "Working directory: $(pwd)"
echo "App contents: $(ls -la /app | head -5)"

# Start cron daemon in background
echo "Starting cron daemon..."
service cron start

# Load cron jobs from configuration file
if [ -f "/app/cronjobs.txt" ]; then
    echo "Loading cron jobs..."
    crontab /app/cronjobs.txt
    echo "Loaded cron jobs:"
    crontab -l
else
    echo "Warning: /app/cronjobs.txt not found - no cron jobs loaded"
fi

# Ensure we're in the right directory
cd /app

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in /app"
    ls -la /app
    exit 1
fi

# Start FastAPI application
echo "Starting FastAPI on port 7000..."
exec uvicorn main:app --host 0.0.0.0 --port 7000 --reload --log-level info
