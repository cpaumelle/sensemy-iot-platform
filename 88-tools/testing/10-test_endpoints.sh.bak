#!/bin/bash

# Enhanced test script for Verdegris IoT platform
# Version: 1.0.0 - 2025-07-12 UTC

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOGFILE="test_endpoints_$(date +%Y%m%d_%H%M%S).log"
echo "Starting tests at $(date)" | tee "$LOGFILE"

declare -A results

# Function to log and print
log() {
    echo -e "$1" | tee -a "$LOGFILE"
}

# Function to test HTTPS endpoint on public domain
test_public_endpoint() {
    local domain=$1
    local endpoint=${2:-/}
    local expected_status=${3:-200}

    log "${YELLOW}Testing public https://${domain}${endpoint}${NC}"

    local status
    status=$(curl -k -s -o /dev/null -w "%{http_code}" "https://${domain}${endpoint}")

    if [ "$status" -eq "$expected_status" ]; then
        log "${GREEN}✓ Status: $status (Success)${NC}"
        results["$domain$endpoint"]="PASS"
    else
        log "${RED}✗ Status: $status (Expected: $expected_status)${NC}"
        log "Verbose curl output:"
        curl -k -v "https://${domain}${endpoint}" 2>&1 | tee -a "$LOGFILE"
        results["$domain$endpoint"]="FAIL"
    fi
    log ""
    sleep 1
}

# Function to test localhost port directly (fallback)
test_localhost_port() {
    local port=$1
    local endpoint=${2:-/health}
    local expected_status=${3:-200}

    log "${YELLOW}Testing localhost http://localhost:${port}${endpoint}${NC}"

    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}${endpoint}")

    if [ "$status" -eq "$expected_status" ]; then
        log "${GREEN}✓ Status: $status (Success)${NC}"
        results["localhost:${port}${endpoint}"]="PASS"
    else
        log "${RED}✗ Status: $status (Expected: $expected_status)${NC}"
        log "Verbose curl output:"
        curl -v "http://localhost:${port}${endpoint}" 2>&1 | tee -a "$LOGFILE"
        results["localhost:${port}${endpoint}"]="FAIL"
    fi
    log ""
    sleep 1
}

# Function to ping domain to check network reachability
test_ping() {
    local domain=$1
    log "${BLUE}Pinging $domain ...${NC}"
    if ping -c 2 -W 2 "$domain" > /dev/null 2>&1; then
        log "${GREEN}✓ Ping successful${NC}"
        results["ping:$domain"]="PASS"
    else
        log "${RED}✗ Ping failed${NC}"
        results["ping:$domain"]="FAIL"
    fi
    log ""
    sleep 1
}

# Public domains and endpoints to test
declare -A public_tests=(
    ["api.sensemy.cloud"]="/health"
    ["devices.sensemy.cloud"]="/health"
    ["ingest.sensemy.cloud"]="/health"
    ["analytics.sensemy.cloud"]="/health"
    ["tools.charliehub.net"]="/adminer/"
    ["app.sensemy.cloud"]="/dashboard.html"
)

# Localhost ports mapped in Docker compose
declare -A localhost_tests=(
    [8100]="/health"  # ingest-service
    [9100]="/health"  # device-manager
    [7100]="/health"  # analytics-service
)

# Run ping tests
for domain in "${!public_tests[@]}"; do
    test_ping "$domain"
done

# Run public HTTPS endpoint tests
for domain in "${!public_tests[@]}"; do
    test_public_endpoint "$domain" "${public_tests[$domain]}"
done

# Run localhost fallback tests
for port in "${!localhost_tests[@]}"; do
    test_localhost_port "$port" "${localhost_tests[$port]}"
done

# Summary report
log "===== Test Summary ====="
pass_count=0
fail_count=0

for key in "${!results[@]}"; do
    if [[ "${results[$key]}" == "PASS" ]]; then
        log "${GREEN}PASS${NC}: $key"
        ((pass_count++))
    else
        log "${RED}FAIL${NC}: $key"
        ((fail_count++))
    fi
done

log ""
log "Total Passed: $pass_count"
log "Total Failed: $fail_count"

if [ $fail_count -eq 0 ]; then
    log "${GREEN}All tests passed successfully! 🎉${NC}"
else
    log "${RED}Some tests failed. Please check logs above and $LOGFILE${NC}"
fi

exit $fail_count