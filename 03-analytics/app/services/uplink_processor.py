# uplink_processor.py
# Version: 0.3.4 - 2025-07-09 13:25 UTC
# Changelog:
# - Fixed "can't adapt type 'dict'" by removing params from db.execute()
# - Relies only on bind values via insert().values()

from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import JSON
from app.database.models import ProcessedUplink
import uuid
from datetime import datetime
import pytz

def store_processed_uplink(db, device_id, timestamp, payload, metrics, context):
    print("[DEBUG] Preparing to insert processed uplink")
    print("device_id:", device_id)
    print("timestamp:", timestamp)
    print("payload:", payload)
    print("metrics:", metrics)
    print("context:", context)

    insert_stmt = insert(ProcessedUplink).values(
        id=str(uuid.uuid4()),
        device_id=device_id,
        timestamp=timestamp,
        payload=JSON(payload),
        network_metrics=JSON(metrics),
        device_type_id=context.get("device_type_id"),
        site_id=context.get("site_id"),
        zone_id=context.get("zone_id"),
        inserted_at=datetime.now(tz=pytz.UTC),
        created_at=datetime.now(tz=pytz.UTC),
        updated_at=datetime.now(tz=pytz.UTC),
    )
    db.execute(insert_stmt)
    db.commit()