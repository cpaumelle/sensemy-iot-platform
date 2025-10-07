#!/bin/bash
# 50-test_devices_api.sh
# Version: 1.5.0 - 2025-08-20 10:35 UTC+2
# Changelog:
# - Restores interactive "Retry with verbose curl" on failures
# - Keeps OpenAPI-aware skipping; resilient (no set -e)
# - Adds RETRY_ON_FAIL=y to auto-run verbose on fail
# - Always shows final summary

# ---------------- Config ----------------
API_BASE="${API_BASE:-https://api3.sensemy.cloud/v1/devices}"
OPENAPI_URL="${OPENAPI_URL:-https://api3.sensemy.cloud/openapi.json}"
VALID_DEV_EUI="${VALID_DEV_EUI:-58A0CB00001088D7}"
RETRY_ON_FAIL="${RETRY_ON_FAIL:-}"

echo "🧪 Running Transform Device API tests..."
echo "🔸 API Base:      $API_BASE"
echo "🔸 OpenAPI:       $OPENAPI_URL"
echo "🔸 Test DevEUI:   $VALID_DEV_EUI"
echo

pass_count=0
fail_count=0
skip_count=0

# --------------- Helpers ----------------
have_jq() { command -v jq >/dev/null 2>&1; }

have_endpoint() {
  # args: path method(lowercase)
  local path="$1" ; local method="$2"
  if ! have_jq; then
    return 2  # unknown
  fi
  (
    curl -s "$OPENAPI_URL" | jq -e --arg p "$path" --arg m "$method" '.paths[$p][$m] // empty' >/dev/null 2>&1
  )
  case $? in
    0) return 0 ;;  # present
    1) return 1 ;;  # not present
    *) return 2 ;;  # unknown (network/parse)
  esac
}

http_code() {
  local method="$1" url="$2" data="${3:-}"
  if [[ "$method" == "GET" ]]; then
    curl -s -o /dev/null -w "%{http_code}" "$url"
  elif [[ -z "$data" ]]; then
    curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url"
  else
    curl -s -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url"
  fi
}

verbose_retry() {
  local method="$1" url="$2" data="${3:-}"
  echo
  echo "🔍 Retrying with verbose curl:"
  if [[ "$method" == "GET" ]]; then
    curl -v "$url"
  elif [[ -z "$data" ]]; then
    curl -v -X "$method" "$url"
  else
    curl -v -X "$method" -H "Content-Type: application/json" -d "$data" "$url"
  fi
  echo
}

run_test() {
  local description="$1" method="$2" url="$3" expect_codes="$4" data="${5:-}"
  echo "🔹 $description ..."
  local code
  code=$(http_code "$method" "$url" "$data")
  if grep -Eq "(^|[[:space:]])$code($|[[:space:]])" <<< "$expect_codes"; then
    echo "✅ PASS ($code)"
    ((pass_count++))
  else
    echo "❌ FAIL ($code)"
    ((fail_count++))

    # Interactive or auto retry with verbose output
    if [[ -n "$RETRY_ON_FAIL" ]]; then
      verbose_retry "$method" "$url" "$data"
    else
      read -p "🔁 Retry with verbose output? (y/N): " retry
      if [[ "$retry" == "y" || "$retry" == "Y" ]]; then
        verbose_retry "$method" "$url" "$data"
      fi
    fi

    # Show JSON detail (non-fatal if fails)
    detail=$(if [[ "$method" == "GET" ]]; then
      curl -s "$url"
    elif [[ -z "$data" ]]; then
      curl -s -X "$method" "$url"
    else
      curl -s -X "$method" -H "Content-Type: application/json" -d "$data" "$url"
    fi)
    if [[ -n "$detail" ]]; then
      echo "🧾 Response body:"
      echo "$detail" | sed -e 's/^/   /'
      if echo "$detail" | grep -q "Device not found"; then
        echo "💡 Hint: Device might be archived. Try unarchiving it first."
      fi
    fi
  fi
}

run_check() {
  # $1 desc  $2 method(lowercase)  $3 openapi_path  $4 url  $5 expected_codes  [$6 data]
  local desc="$1" lo_method="$2" path="$3" url="$4" expect="$5" data="${6:-}"
  have_endpoint "$path" "$lo_method"
  local ep=$?
  case "$ep" in
    0) run_test "$desc" "$(tr '[:lower:]' '[:upper:]' <<< "$lo_method")" "$url" "$expect" "$data" ;;
    1) echo "⏭️  SKIP $desc (not in OpenAPI)"; ((skip_count++)) ;;
    2) echo "ℹ️  OpenAPI unknown for: $path — running test anyway"
       run_test "$desc" "$(tr '[:lower:]' '[:upper:]' <<< "$lo_method")" "$url" "$expect" "$data" ;;
  esac
}

# ---------------- Tests ------------------
echo "➡️  Test 1: GET /devices"
run_test "GET /devices" "GET" "$API_BASE" "200"
echo

echo "➡️  Test 2: GET /devices/device-types"
run_check "GET /devices/device-types" "get" "/v1/devices/device-types" \
  "$API_BASE/device-types" "200"
echo

echo "➡️  Test 3: GET /devices/locations/hierarchy"
run_check "GET /devices/locations/hierarchy" "get" "/v1/devices/locations/hierarchy" \
  "$API_BASE/locations/hierarchy" "200"
echo

echo "➡️  Test 4: GET /devices/full-metadata"
run_check "GET /devices/full-metadata" "get" "/v1/devices/full-metadata" \
  "$API_BASE/full-metadata" "200"
echo

echo "➡️  Test 5: GET /devices/{deveui}/suggestions"
run_check "GET /devices/{deveui}/suggestions" "get" "/v1/devices/{deveui}/suggestions" \
  "$API_BASE/$VALID_DEV_EUI/suggestions" "200"
echo

echo "➡️  Test 6: PUT /devices/{deveui}"
UPDATE_NAME="updated-$(date +%s)"
run_check "PUT /devices/{deveui}" "put" "/v1/devices/{deveui}" \
  "$API_BASE/$VALID_DEV_EUI" "200 201 204 404" \
  "{\"name\":\"$UPDATE_NAME\"}"
echo

# --------------- Summary ----------------
echo "📋 Test Summary:"
echo "✅ Passed: $pass_count"
echo "⏭️  Skipped: $skip_count"
echo "❌ Failed: $fail_count"

# Non-zero exit if any failed
[[ $fail_count -eq 0 ]] || exit 1
