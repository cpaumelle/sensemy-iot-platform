#!/bin/bash
# WMC Gateway QR Scanner - Deployment Script
# Version: 1.0.0
# Created: 2025-08-20 16:45:00 UTC

echo "🚀 Deploying WMC Gateway QR Scanner Service..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the v4-iot-pipeline directory"
    exit 1
fi

# Check for required environment variables
if [ -z "$WMC_USERNAME" ] || [ -z "$WMC_PASSWORD" ]; then
    echo "⚠️ Warning: WMC credentials not set in environment"
    echo "Please set WMC_USERNAME and WMC_PASSWORD in your .env file"
fi

# Build and start the service
echo "🔧 Building WMC Gateway Scanner service..."
docker-compose build wmc-gateway-scanner --no-cache

echo "🚀 Starting WMC Gateway Scanner service..."
docker-compose up -d wmc-gateway-scanner

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps wmc-gateway-scanner

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost:7300/health >/dev/null 2>&1; then
    echo "✅ WMC Gateway Scanner service is healthy"
else
    echo "⚠️ Health check failed, checking logs..."
    docker-compose logs --tail 20 wmc-gateway-scanner
fi

# Test WMC connectivity
echo "🔍 Testing WMC API connectivity..."
curl -s http://localhost:7300/api/v1/auth/test-connection | jq . || echo "WMC connection test completed"

echo ""
echo "🎉 WMC Gateway QR Scanner deployment completed!"
echo ""
echo "📋 Access Information:"
echo "  🔍 QR Scanner UI:    http://localhost:7300"
echo "  📖 API Docs:         http://localhost:7300/docs"
echo "  🏥 Health Check:     http://localhost:7300/health"
echo "  🌐 Production URL:   https://gateway-scanner.sensemy.cloud (after reverse proxy)"
echo ""
echo "🔧 Development Commands:"
echo "  docker logs wmc-gateway-scanner"
echo "  docker exec -it wmc-gateway-scanner /bin/bash"
echo "  curl http://localhost:7300/api/v1/gateways/lookup/YOUR_GATEWAY_EUI"
echo ""
echo "📱 Usage Instructions:"
echo "  1. Open the web app on your mobile device"
echo "  2. Allow camera permissions when prompted"
echo "  3. Scan a gateway QR code or enter EUI manually"
echo "  4. View real-time gateway status from WMC API"
