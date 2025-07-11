#!/bin/bash
# 3-clean-volumes-v4.sh - Remove V4 Docker volumes
# Version: 0.1.0
# Updated: 2025-07-10 23:08 UTC

cd "$(dirname "$0")/.."

echo "⚠️  This will permanently delete all V4 data volumes:"
echo "   - ingest-db-data-v4"
echo "   - device-db-data-v4"
echo "   - analytics-db-data-v4"
read -p "❓ Proceed? (y/N): " confirm

if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
  docker volume rm ingest-db-data-v4 device-db-data-v4 analytics-db-data-v4
  echo "✅ V4 volumes deleted."
else
  echo "❌ Aborted. Volumes not deleted."
fi
