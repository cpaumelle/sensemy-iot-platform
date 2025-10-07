#!/bin/bash
# Build script with auto-incrementing version
# Version: 1.0.0 - 2025-08-11 17:45:00 UTC

set -e

echo "🚀 SenseMy IoT Platform - Build with Version"
echo "============================================"

# Get current timestamp
BUILD_TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
BUILD_DATE=$(date -u +"%Y%m%d")
BUILD_TIME=$(date -u +"%H%M%S")

# Version file path
VERSION_FILE="src/version.json"

# Read current version or create if doesn't exist
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(jq -r '.version' "$VERSION_FILE" 2>/dev/null || echo "4.0.0")
    CURRENT_BUILD=$(jq -r '.build' "$VERSION_FILE" 2>/dev/null || echo "0")
else
    CURRENT_VERSION="4.0.0"
    CURRENT_BUILD="0"
fi

# Increment build number
NEW_BUILD=$((CURRENT_BUILD + 1))

# Create version info
cat > "$VERSION_FILE" << EOV
{
  "version": "$CURRENT_VERSION",
  "build": $NEW_BUILD,
  "buildTimestamp": "$BUILD_TIMESTAMP",
  "buildDate": "$BUILD_DATE",
  "buildTime": "$BUILD_TIME",
  "buildNumber": "${BUILD_DATE}.${NEW_BUILD}",
  "gitCommit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "environment": "production"
}
EOV

echo "📦 Version: $CURRENT_VERSION"
echo "🔢 Build: $NEW_BUILD"
echo "🕒 Timestamp: $BUILD_TIMESTAMP"
echo "📋 Build Number: ${BUILD_DATE}.${NEW_BUILD}"

# Copy version to public directory so it's included in build
mkdir -p public
cp "$VERSION_FILE" public/

# Set environment variables for build
export VITE_VERSION="$CURRENT_VERSION"
export VITE_BUILD_NUMBER="$NEW_BUILD"
export VITE_BUILD_TIMESTAMP="$BUILD_TIMESTAMP"
export VITE_BUILD_ID="${BUILD_DATE}.${NEW_BUILD}"

# Run the actual build
echo "🔨 Starting Vite build..."
npm run build

# Copy version.json to dist for nginx to serve
cp "$VERSION_FILE" dist/

echo "✅ Build complete!"
echo "📋 Build ID: ${BUILD_DATE}.${NEW_BUILD}"
echo "🌐 Version file available at: /version.json"
