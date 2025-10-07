#!/bin/bash
# 20-test-ui-workflow.sh
# Version: 1.2.2 - 2025-07-16 15:25 UTC

set -e  # Exit on any error

LOGFILE="test_ui_workflow_$(date +%Y%m%d_%H%M%S).log"
API_BASE="https://api2.sensemy.cloud"
APP_BASE="https://app2.sensemy.cloud"
ANALYTICS_BASE="https://dev.sensemy.cloud/analytics"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "Starting UI workflow test at $(date -u)" | tee -a "$LOGFILE"

print_status() { echo -e "${BLUE}[TEST]${NC} $1" | tee -a "$LOGFILE"; }
print_success() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$LOGFILE"; }
print_error() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "$LOGFILE"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOGFILE"; }

test_api_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_fields=$4
    local data=$5

    print_status "Testing $method $endpoint - $description"

    local curl_cmd="curl -s -w '%{http_code}' -X $method '$API_BASE$endpoint'"
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi

    local response=$(eval $curl_cmd)
    local http_code="${response: -3}"
    local body="${response%???}"

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        print_success "HTTP $http_code - Endpoint responding"
        if [ -n "$expected_fields" ]; then
            for field in $expected_fields; do
                if echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if '$field' in str(data) else 1)" 2>/dev/null; then
                    print_success "  ✓ Field '$field' present"
                else
                    print_warning "  ? Field '$field' not found"
                fi
            done
        fi
        echo "  📄 Response preview: $(echo "$body" | head -c 100)..."
    else
        print_error "HTTP $http_code - $body"
    fi
    echo ""
}

echo "🔌 PART 1: API ENDPOINT TESTS"            | tee -a "$LOGFILE"
echo "=============================="           | tee -a "$LOGFILE"

test_api_endpoint "GET" "/v1/summary" "Dashboard summary data" "total_devices uplinks_24h"
test_api_endpoint "GET" "/v1/sites" "Sites list" "id name"
test_api_endpoint "GET" "/v1/devices" "Devices list" "deveui status"
test_api_endpoint "GET" "/v1/zones" "Zones with hierarchy" "full_path location"
test_api_endpoint "GET" "/v1/locations/hierarchy" "Location hierarchy" "floors"

echo ""                                         | tee -a "$LOGFILE"
echo "🌐 PART 2: FRONTEND FILE AVAILABILITY"    | tee -a "$LOGFILE"
echo "====================================="    | tee -a "$LOGFILE"

frontend_files=("index.html" "sites.html" "locations.html" "devices.html" "js/api.js" "css/style.css")
for file in "${frontend_files[@]}"; do
    print_status "Testing frontend file: $file"
    http_code=$(curl -s -o /dev/null -w '%{http_code}' "$APP_BASE/$file")
    if [ "$http_code" -eq 200 ]; then
        print_success "✓ $file accessible (HTTP $http_code)"
    else
        print_error "✗ $file not accessible (HTTP $http_code)"
    fi
done

echo ""                                 | tee -a "$LOGFILE"
echo "📊 PART 3: DATA INTEGRATION TEST" | tee -a "$LOGFILE"
echo "================================" | tee -a "$LOGFILE"

summary_response=$(curl -s "$API_BASE/v1/summary")
total_devices_summary=$(echo "$summary_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_devices', 0))" 2>/dev/null || echo "0")

devices_response=$(curl -s "$API_BASE/v1/devices")
total_devices_list=$(echo "$devices_response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$total_devices_summary" -eq "$total_devices_list" ]; then
    print_success "Device counts match: Summary=$total_devices_summary, List=$total_devices_list"   | tee -a "$LOGFILE"
else
    print_warning "Device count mismatch: Summary=$total_devices_summary, List=$total_devices_list" | tee -a "$LOGFILE"
fi

zones_response=$(curl -s "$API_BASE/v1/zones")
zones_with_hierarchy=$(echo "$zones_response" | python3 -c "import sys, json; print(sum(1 for z in json.load(sys.stdin) if 'undefined' not in z.get('full_path', '')))" 2>/dev/null || echo "0")
total_zones=$(echo "$zones_response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

if [ "$zones_with_hierarchy" -eq "$total_zones" ] && [ "$total_zones" -gt 0 ]; then
    print_success "All $total_zones zones have proper hierarchy"    | tee -a "$LOGFILE"
elif [ "$total_zones" -eq 0 ]; then
    print_warning "No zones found in system"                        | tee -a "$LOGFILE"
else
    print_warning "$zones_with_hierarchy/$total_zones zones have proper hierarchy"  | tee -a "$LOGFILE"
fi

echo ""                                         | tee -a "$LOGFILE"
echo "📈 PART 4: ANALYTICS INTEGRATION TESTS"   | tee -a "$LOGFILE"
echo "======================================"   | tee -a "$LOGFILE"

print_status "Posting test metadata to /twinning"   | tee -a "$LOGFILE"
twinning_payload='{"deveui":"0004A30B00FB6713","device_type_id":1,"site_id":1,"floor_id":2,"room_id":3,"zone_id":10,"last_gateway":"fr-gw-2"}'
twinning_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ANALYTICS_BASE/twinning" -H "Content-Type: application/json" -d "$twinning_payload")

[ "$twinning_response" -eq 200 ] && print_success "✓ /twinning accepted test metadata" || print_error "❌ /twinning failed with HTTP $twinning_response"   | tee -a "$LOGFILE"

print_status "Posting test uplink to /uplinks"  | tee -a "$LOGFILE"
uplink_payload='{"deveui":"0004A30B00FB6713","timestamp":"2025-07-07T18:00:00Z","decoded_payload":{"battery":3.2,"motion":false},"raw_payload":"0167FF03","device_type":"IMBuildings People Counter"}'
uplink_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ANALYTICS_BASE/uplinks" -H "Content-Type: application/json" -d "$uplink_payload")

[ "$uplink_response" -eq 200 ] && print_success "✓ /uplinks received and processed test data" || print_error "❌ /uplinks failed with HTTP $uplink_response"

echo ""                                                                             | tee -a "$LOGFILE"
echo "✅ Completed all tests. Now review warnings, then test in browser if needed." | tee -a "$LOGFILE"
echo "📄 Full log saved to: $LOGFILE"                                               | tee -a "$LOGFILE"