# models.py
# Version: 0.1.0 - 2025-07-09 13:50 UTC
# Changelog:
# - Initial SQLAlchemy models for `processed_uplinks` and `device_context`

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, TIMESTAMP, func, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.database.connections import Base

class ProcessedUplink(Base):
    __tablename__ = "processed_uplinks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    decoded_fields = Column(JSONB)
    normalized_fields = Column(JSONB)
    network_metrics = Column(JSONB)
    device_type_id = Column(Integer)
    site_id = Column(Integer)
    zone_id = Column(Integer)
    inserted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class DeviceContext(Base):
    __tablename__ = "device_context"

    id = Column(Integer, primary_key=True)
    deveui = Column(Text, nullable=False, unique=True)
    device_type_id = Column(Integer, nullable=False)
    site_id = Column(Integer)
    zone_id = Column(Integer)
    firmware_version = Column(Text)
    battery_status = Column(Text)
    status = Column(Text)
    first_seen = Column(TIMESTAMP(timezone=True))
    last_seen = Column(TIMESTAMP(timezone=True))
    last_communication_timestamp = Column(TIMESTAMP(timezone=True))
    location_confidence = Column(Numeric(5, 2))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
