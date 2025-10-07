#!/bin/bash
# 3-clean-volumes-.sh - Remove V4 Docker volumes
# Version: 0.1.0
# Updated: 2025-07-10 23:08 UTC

cd "$(dirname "$0")/.."

echo "⚠️  This will permanently delete all V4 data volumes:"
echo "   - ingest-db-data-"
echo "   - device-db-data-"
echo "   - analytics-db-data-"
read -p "❓ Proceed? (y/N): " confirm

if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
  docker volume rm ingest-db-data- device-db-data- analytics-db-data-
  echo "✅ V4 volumes deleted."
else
  echo "❌ Aborted. Volumes not deleted."
fi
