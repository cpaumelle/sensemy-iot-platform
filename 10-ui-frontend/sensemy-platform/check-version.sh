#!/bin/bash
# Quick version check script
# Version: 1.0.0 - 2025-08-11 18:00:00 UTC

echo "🔍 SenseMy IoT Platform - Version Check"
echo "======================================"

# Local version
echo "📍 Local version:"
LOCAL_VERSION=$(curl -s http://localhost:8801/version.json 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$LOCAL_VERSION" | jq .
else
    echo "❌ Could not reach local version endpoint"
fi

echo

# External version
echo "🌍 External version:"
EXTERNAL_VERSION=$(curl -s https://app2.sensemy.cloud/version.json 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$EXTERNAL_VERSION" | jq .
else
    echo "❌ Could not reach external version endpoint"
fi

echo

# Compare
if [ "$LOCAL_VERSION" = "$EXTERNAL_VERSION" ] && [ -n "$LOCAL_VERSION" ]; then
    echo "✅ Local and external versions match!"
else
    echo "⚠️  Local and external versions differ or unavailable"
fi
