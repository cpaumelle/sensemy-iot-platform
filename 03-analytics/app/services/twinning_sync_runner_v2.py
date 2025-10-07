# ─── Version: 1.0.0 ─────────────────────────────────────────────────────────────
# File: twinning_sync_runner.py
# Purpose: Standalone utility script to sync device metadata to the analytics receiver.
# Usage:
#   - Run manually:       python services/twinning_sync_runner.py
#   - Run via cron:       @daily python /app/services/twinning_sync_runner.py
#   - Used by API:        import and call sync_single_device(deveui)
# Location: services/
# Author: CharlieHub IoT Team
# Date: 2025-07-08

import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# ─── Load environment variables ────────────────────────────────────────────────
load_dotenv()

DB_HOST = os.getenv("DEVICE_DB_HOST", "device-database")
DB_PORT = os.getenv("DEVICE_DB_INTERNAL_PORT", os.getenv("DEVICE_DB_PORT", "5432"))
DB_NAME = os.getenv("DEVICE_DB_NAME", "device_db")
DB_USER = os.getenv("DEVICE_DB_USER", "iot")
DB_PASS = os.getenv("DEVICE_DB_PASSWORD", "secret")
ANALYTICS_URL = os.getenv("ANALYTICS_RECEIVER_URL", "http://analytics-service:7000/twinning")

# ─── Build payload structure from device row ───────────────────────────────────

def make_payload(device: dict) -> dict:
    return {
        "deveui": device["deveui"],
        "device_type_id": device["device_type_id"],
        "site_id": device["site_id"],
        "floor_id": device["floor_id"],
        "room_id": device["room_id"],
        "zone_id": device["zone_id"],
        "gateway_eui": device.get("gateway_eui"),
        "gateway_network_name": device.get("gateway_network_name"),
        "last_gateway": device.get("last_gateway"),
        "firmware_version": device.get("firmware_version"),
        "battery_status": device.get("battery_status"),
        "status": device["status"],
        "device_family": device.get("device_family"),
        "unpacker_module": device.get("unpacker_module_name"),
        "unpacker_function": device.get("unpacker_function_name"),
        "device_icon": device.get("device_icon"),
    }

# ─── Function: Sync all eligible devices to analytics-service ────────────────

def sync_all_devices():
    """Batch sync all devices with device_type_id to analytics-service"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        print("[INFO] Connected to device database successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return

    success = 0
    failure = 0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                d.deveui,
                d.device_type_id,
                d.zone_id,
                z.room_id,
                r.floor_id,
                f.site_id,
                d.name AS device_name,
                g.eui AS gateway_eui,
                g.network_name AS gateway_network_name,
                g.description AS last_gateway,
                t.device_family,
                t.unpacker_module_name,
                t.unpacker_function_name,
                t.icon_name AS device_icon,
                d.firmware_version,
                d.battery_status,
                d.status
            FROM analytics.device_context d
            LEFT JOIN devices.device_types t ON d.device_type_id = t.id
            LEFT JOIN devices.zones z ON d.zone_id = z.id
            LEFT JOIN devices.rooms r ON z.room_id = r.id
            LEFT JOIN devices.floors f ON r.floor_id = f.id
            LEFT JOIN devices.gateways g ON d.gateway_id = g.id
            WHERE d.device_type_id IS NOT NULL
        """)
        devices = cur.fetchall()

    print(f"[INFO] Found {len(devices)} devices to twin.")

    for device in devices:
        payload = make_payload(device)
        try:
            r = requests.post(ANALYTICS_URL, json=payload, timeout=5)
            if r.status_code == 200:
                print(f"[✓] {device['deveui']} → {r.status_code}")
                success += 1
            else:
                print(f"[!] {device['deveui']} → {r.status_code}: {r.text}")
                failure += 1
        except Exception as e:
            print(f"[ERROR] Failed to send {device['deveui']}: {e}")
            failure += 1

    print(f"\n[SUMMARY] Success: {success}, Failures: {failure}")


# ─── Function: Sync one device by deveui (used in API or CLI) ──────────────────

def sync_single_device(deveui: str):
    """Sync a single device to analytics-service by deveui"""
    try:
        with psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        ) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        d.deveui,
                        d.device_type_id,
                        d.zone_id,
                        z.room_id,
                        r.floor_id,
                        f.site_id,
                        g.eui AS gateway_eui,
                        g.network_name AS gateway_network_name,
                        g.description AS last_gateway,
                        t.device_family,
                        t.unpacker_module_name,
                        t.unpacker_function_name,
                        t.icon_name AS device_icon,
                        d.firmware_version,
                        d.battery_status,
                        d.status
                    FROM analytics.device_context_with_status d
                    LEFT JOIN devices.device_types t ON d.device_type_id = t.id
                    LEFT JOIN devices.zones z ON d.zone_id = z.id
                    LEFT JOIN devices.rooms r ON z.room_id = r.id
                    LEFT JOIN devices.floors f ON r.floor_id = f.id
                    LEFT JOIN devices.gateways g ON d.gateway_id = g.id
                    WHERE d.device_type_id IS NOT NULL AND d.deveui = %s
                """, (deveui,))
                device = cur.fetchone()

        if not device:
            print(f"[WARN] No twinning data found for {deveui}")
            return

        payload = make_payload(device)

        r = requests.post(ANALYTICS_URL, json=payload, timeout=5)
        if r.status_code == 200:
            print(f"[✓] Twinned {deveui} → {r.status_code}")
        else:
            print(f"[!] Twinning {deveui} → {r.status_code}: {r.text}")

    except Exception as e:
        print(f"[ERROR] Database or network error while syncing {deveui}: {e}")


# ─── Manual Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[INFO] Starting full device metadata sync to analytics-service...\n")
    sync_all_devices()
