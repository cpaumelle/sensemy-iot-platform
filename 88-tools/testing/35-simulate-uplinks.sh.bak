#!/bin/bash
set -e

echo "📡 Choose the uplink to simulate:"
select source in "actility" "netmore"; do
  case $source in
    actility)
      file="32-actility_payload_test.json"
      key="Time"
      deveui_field="DevEUI"
      payload_field="payload_hex"
      timestamp_field=".DevEUI_uplink.Time"
      randomize_field=".DevEUI_uplink.payload_hex"
      break
      ;;
    netmore)
      file="31-netmore_payload_test.json"
      key="timestamp"
      deveui_field="devEui"
      payload_field="payload"
      timestamp_field=".timestamp"
      randomize_field=".payload"
      break
      ;;
    *) echo "❌ Invalid option. Try again.";;
  esac
done

cd "$(dirname "$0")"

# Load original payload
original=$(cat "$file")

# Generate current timestamp in ISO format (UTC)
now=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# Generate 2 random bytes (4 hex chars)
rand_hex=$(openssl rand -hex 2)

# Patch JSON with updated timestamp and randomized payload tail
patched=$(echo "$original" | jq \
  --arg time "$now" \
  --arg rand "$rand_hex" \
  --arg field "$payload_field" \
  --argjson is_actility $([[ "$source" == "actility" ]] && echo true || echo false) '
  if $is_actility then
    .DevEUI_uplink.Time = $time |
    .DevEUI_uplink.payload_hex |= (.[: -4] + $rand)
  else
    .timestamp = $time |
    .payload |= (.[: -4] + $rand)
  end
')

# Save to temp file
tmpfile="/tmp/simulated_${source}_uplink.json"
echo "$patched" > "$tmpfile"

# Send via curl
echo "🚀 Sending simulated $source uplink..."
curl -s -X POST "http://localhost:8100/uplink?source=$source" \
  -H "Content-Type: application/json" \
  --data-binary "@$tmpfile"

echo -e "\n✔️  $source uplink sent using $tmpfile"
