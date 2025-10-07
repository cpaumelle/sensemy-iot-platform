#!/bin/bash
# check-env.sh - Env Validator and Setup
# Version: 0.3.0 - 2025-07-15 23:58 UTC

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Env file $ENV_FILE not found"
  exit 1
fi

# Load environment, skip UID/GID redefinition
set -a
grep -vE '^(UID|GID)=' "$ENV_FILE" > /tmp/.env.tmp
source /tmp/.env.tmp
rm /tmp/.env.tmp
set +a

echo "🔍 Validating required variables..."

MISSING=0
REQUIRED_VARS=(
  INGEST_PORT DEVICE_MANAGER_PORT ANALYTICS_PORT
  ADMINER_PORT UI_FRONTEND_PORT
  INGEST_DB_PORT DEVICE_DB_PORT ANALYTICS_DB_PORT
  INGEST_DB_NAME DEVICE_DB_NAME ANALYTICS_DB_NAME
  INGEST_DB_USER DEVICE_DB_USER ANALYTICS_DB_USER
  INGEST_DB_PASSWORD DEVICE_DB_PASSWORD ANALYTICS_DB_PASSWORD
  NETWORK_NAME DOMAIN_ROOT TLS_EMAIL
  DEVICE_API_BASE_URL
  INGEST_RECEIVER_URL_ACTILITY
  INGEST_RECEIVER_URL_NETMORE
  ANALYTICS_RECEIVER_URL
  DEVICE_MANAGER_URL
  DATABASE_URL
  UI_STATIC_PATH
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

# --- Docker network checks ---
if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "🛠 Creating Docker network: $NETWORK_NAME"
  docker network create "$NETWORK_NAME"
fi

if ! docker network inspect charliehub_net >/dev/null 2>&1; then
  echo "🛠 Creating Docker network: charliehub_net"
  docker network create charliehub_net
fi

echo "🔍 Checking for port conflicts..."
HOST_PORTS=(
  $INGEST_PORT $DEVICE_MANAGER_PORT $ANALYTICS_PORT
  $ADMINER_PORT $UI_FRONTEND_PORT
  $INGEST_DB_PORT $DEVICE_DB_PORT $ANALYTICS_DB_PORT
)

CONFLICT=0
for PORT in "${HOST_PORTS[@]}"; do
  if [ -n "$PORT" ] && ss -tuln | grep -q ":$PORT\b"; then
    echo "❌ Port $PORT is already in use"
    CONFLICT=1
  fi
done

if [ "$CONFLICT" -eq 1 ]; then
  echo "❌ One or more ports are already bound"
  exit 1
else
  echo "✅ No host port conflicts detected"
fi

echo "✅ .env validation complete"