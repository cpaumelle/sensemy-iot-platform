#!/bin/bash
# check-env-v4.sh - V4 Env Validator
# Version: 0.2.1
# Updated: 2025-07-10 22:55 UTC

ENV_FILE="../.env.v4"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Env file $ENV_FILE not found"
  exit 1
fi

# Load environment, skip UID/GID redefinition
set -a
grep -vE '^(UID|GID)=' "$ENV_FILE" > /tmp/.env.v4.tmp
source /tmp/.env.v4.tmp
rm /tmp/.env.v4.tmp
set +a

echo "🔍 Validating required variables..."

MISSING=0
REQUIRED_VARS=(
  V4_INGEST_PORT V4_DEVICE_MANAGER_PORT V4_ANALYTICS_PORT
  V4_CADDY_HTTP_PORT V4_CADDY_HTTPS_PORT V4_ADMINER_PORT
  V4_INGEST_DB_PORT V4_DEVICE_DB_PORT V4_ANALYTICS_DB_PORT
  V4_INGEST_DB_NAME V4_DEVICE_DB_NAME V4_ANALYTICS_DB_NAME
  V4_INGEST_DB_USER V4_DEVICE_DB_USER V4_ANALYTICS_DB_USER
  V4_INGEST_DB_PASSWORD V4_DEVICE_DB_PASSWORD V4_ANALYTICS_DB_PASSWORD
  V4_NETWORK_NAME V4_DOMAIN_ROOT V4_TLS_EMAIL
)

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Missing: $var"
    MISSING=1
  fi
done

if [ "$MISSING" -eq 1 ]; then
  echo "❌ Some required environment variables are missing"
  exit 1
else
  echo "✅ All required environment variables are set"
fi

echo "🔍 Checking for port conflicts..."
HOST_PORTS=(
  $V4_INGEST_PORT $V4_DEVICE_MANAGER_PORT $V4_ANALYTICS_PORT
  $V4_CADDY_HTTP_PORT $V4_CADDY_HTTPS_PORT $V4_ADMINER_PORT
  $V4_INGEST_DB_PORT $V4_DEVICE_DB_PORT $V4_ANALYTICS_DB_PORT
)

for PORT in "${HOST_PORTS[@]}"; do
  if ss -tuln | grep -q ":$PORT\b"; then
    echo "❌ Port $PORT is already in use"
    CONFLICT=1
  fi
done

if [ "$CONFLICT" == "1" ]; then
  echo "❌ One or more ports are already bound"
  exit 1
else
  echo "✅ No host port conflicts detected"
fi

echo "✅ .env.v4 validation complete"
