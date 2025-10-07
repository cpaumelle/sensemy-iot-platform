# 03-analytics-service/Dockerfile
# Version: 1.0.0 - 2025-08-09 12:15 UTC
# Based on: 2b-transform-server/Dockerfile v0.2.4
# Changelog:
# - Adapted transform Dockerfile for analytics service
# - Added analytics-specific dependencies
# - Maintained cron setup for materialized view refresh

FROM python:3.11-slim

# ─── Env Setup ─────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# ─── Copy App and Requirements ─────────────────────────────
COPY ./app/ /app/
COPY requirements.txt /app/
COPY entrypoint.sh /app/entrypoint.sh
COPY ./cronjobs.txt /app/cronjobs.txt

# ─── System Dependencies ───────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    cron \
    curl \
    nano \
    && rm -rf /var/lib/apt/lists/*

# ─── Python Dependencies ───────────────────────────────────
RUN pip install --no-cache-dir -r requirements.txt

# ─── Make Scripts Executable ───────────────────────────────
RUN chmod +x /app/entrypoint.sh

# ─── Setup Cron ────────────────────────────────────────────
RUN touch /var/log/cron.log /var/log/cron_heartbeat.log && \
    chmod 666 /var/log/cron*.log && \
    crontab /app/cronjobs.txt

# ─── Entrypoint ────────────────────────────────────────────
ENTRYPOINT ["/app/entrypoint.sh"]
