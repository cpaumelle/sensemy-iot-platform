# Version: 0.1.0 - 2025-07-08
# Provides normalization from Actility uplink format to internal format

from datetime import datetime

def normalize_actility_payload(data):
    try:
        device_id = data.get("LrnDevEui")
        timestamp = data.get("Time")
        payload_hex = data.get("payload")

        # Optional metrics from Actility (not always present)
        metrics = {
            "LrnFPort": data.get("LrnFPort"),
            "AS_ID": data.get("AS_ID"),
            "LrnInfos": data.get("LrnInfos"),
            "Token": data.get("Token"),
        }

        return {
            "device_id": device_id,
            "received_at": timestamp,
            "payload": {"raw": payload_hex},
            "network_metrics": metrics,
        }
    except Exception as e:
        raise ValueError(f"Normalization failed: {e}")
