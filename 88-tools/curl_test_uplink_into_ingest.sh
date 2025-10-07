#!/bin/bash

# ─── Device Info ────────────────────────────────────────────────────────────────
DEVEUI="58A0CB00001091DE"
FIXED_HEX="08fb3841ffffff"
RANDOM_BYTE=$(printf "%02x" $((RANDOM % 256)))
PAYLOAD_HEX="${FIXED_HEX}${RANDOM_BYTE}"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── JSON Payload ──────────────────────────────────────────────────────────────
JSON=$(cat <<EOF
{
  "DevEUI_uplink": {
    "DevEUI": "${DEVEUI}",
    "Time": "${NOW}",
    "FPort": 103,
    "payload_hex": "${PAYLOAD_HEX}",
    "LrrRSSI": -97.0,
    "LrrSNR": 10.25,
    "Lrrid": "1000BCDC",
    "CustomerData": {
      "alr": { "pro": "BROW/TB100", "ver": "1" },
      "doms": [{"g": "Clients", "n": "Charles R&D Product"}],
      "name": "91DE Garden shed"
    },
    "DriverCfg": {
      "app": { "mId": "tbhh100", "pId": "os1-brow", "ver": "1" },
      "mod": { "mId": "tbhh100", "pId": "browan", "ver": "1" }
    },
    "BaseStationData": {
      "doms": [{"g": "Clients", "n": "CP's Gateways"}],
      "name": "CP-Dinard-7076FF006404010B"
    },
    "PayloadEncryption": 0
  }
}
EOF
)

# ─── CURL POST ─────────────────────────────────────────────────────────────────
curl -X POST "https://ingest.sensemy.cloud/uplink?source=actility" \
  -H "Content-Type: application/json" \
  -d "$JSON"

echo
