# Version: 0.3.0 - 2025-07-09 11:55 UTC
# Changelog:
# - Switched from raw psycopg2 to SQLAlchemy session-based queries
# - Uses analytics.device_context table

from sqlalchemy.orm import Session
from sqlalchemy import text

def fetch_device_context(db: Session, deveui: str):
    query = text("""
        SELECT device_type_id, site_id, zone_id
        FROM analytics.device_context
        WHERE deveui = :deveui
    """)
    result = db.execute(query, {"deveui": deveui}).fetchone()
    if result:
        return {
            "device_type_id": result.device_type_id,
            "site_id": result.site_id,
            "zone_id": result.zone_id
        }
    return None