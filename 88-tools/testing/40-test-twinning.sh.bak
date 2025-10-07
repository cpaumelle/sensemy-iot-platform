#!/bin/bash

# 40-test-twinning.sh
# Purpose: Test the twinning functionality in twinning.py

# Set the base URL for the API
API_BASE_URL="http://localhost:8000/v1"

# Function to create a resource
create_resource() {
    local resource=$1
    local payload=$2
    curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$API_BASE_URL/$resource"
}

# Create sample sites, floors, rooms, and zones
create_resource "sites" '{"name": "Site 1"}'
create_resource "floors" '{"name": "Floor 1", "site_id": 1}'
create_resource "rooms" '{"name": "Room 1", "floor_id": 1}'
create_resource "zones" '{"name": "Zone 1", "room_id": 1}'

# Add the parent directory of the services module to the Python module search path
export PYTHONPATH="$PYTHONPATH:$(pwd)/../../02-device-manager/app"

# Run tests for twinning.py
python3 - <<EOF
from services.twinning import get_twinning_info, enrich_uplink_with_twinning

# Test case 1: Get twinning info for a device
twinning_info = get_twinning_info('TEST123XACTILITY')
assert twinning_info['deveui'] == 'TEST123XACTILITY'
assert twinning_info['device_type_id'] == 1
assert twinning_info['zone_id'] == 1
# Add more assertions for other twinning fields

print("Test case 1 passed: Get twinning info")

# Test case 2: Enrich uplink data with twinning info
uplink_data = {
    'deveui': 'TEST123XACTILITY',
    # Add other uplink fields
}
enriched_data = enrich_uplink_with_twinning(uplink_data, twinning_info)
assert enriched_data['device_context']['deveui'] == 'TEST123XACTILITY'
assert enriched_data['device_context']['device_type_id'] == 1
assert enriched_data['device_context']['zone_id'] == 1
# Add more assertions for other enriched fields

print("Test case 2 passed: Enrich uplink data")

print("All test cases passed!")
EOF