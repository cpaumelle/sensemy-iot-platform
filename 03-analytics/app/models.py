# app/models.py - analytics
# Version: 2.0.0 - 2025-08-11 19:00:00 UTC
# Based on: Transform service model patterns
# Analytics schema models for CRUD operations and data queries
# Added: Environmental analytics materialized view models

from sqlalchemy import (
    Column, String, Integer, Boolean, Float, Text, ForeignKey, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base

# ═══════════════════════════════════════════════════════════════════
# ANALYTICS SCHEMA MODELS (Based on uploaded schema)
# ═══════════════════════════════════════════════════════════════════

class AggregationPattern(Base):
    __tablename__ = "aggregation_patterns"
    __table_args__ = {"schema": "analytics"}

    pattern_id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    value_path = Column(Text, nullable=False)
    data_type = Column(Text, nullable=False)  # float, int, bool, text
    aggregation_method = Column(Text, nullable=False)  # avg_per_hour, sum_delta
    unit = Column(Text, nullable=True)
    is_cumulative = Column(Boolean, default=False)
    reset_hour = Column(Integer, default=0)

    # Relationships
    device_mappings = relationship("DeviceAggregationMap", back_populates="pattern")
    alert_definitions = relationship("AlertDefinition", back_populates="pattern")

    def as_dict(self):
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "value_path": self.value_path,
            "data_type": self.data_type,
            "aggregation_method": self.aggregation_method,
            "unit": self.unit,
            "is_cumulative": self.is_cumulative,
            "reset_hour": self.reset_hour,
        }

class DeviceAggregationMap(Base):
    __tablename__ = "device_aggregation_map"
    __table_args__ = {"schema": "analytics"}

    device_type_id = Column(Integer, primary_key=True)
    pattern_id = Column(Integer, ForeignKey("analytics.aggregation_patterns.pattern_id"), primary_key=True)
    field_alias = Column(Text, nullable=False)

    # Relationships
    pattern = relationship("AggregationPattern", back_populates="device_mappings")

    def as_dict(self):
        return {
            "device_type_id": self.device_type_id,
            "pattern_id": self.pattern_id,
            "field_alias": self.field_alias,
        }

class DataDictionary(Base):
    __tablename__ = "data_dictionary"
    __table_args__ = {"schema": "analytics"}

    dict_id = Column(Integer, primary_key=True, index=True)
    device_type_id = Column(Integer, nullable=True)  # NULL = global field
    field_name = Column(Text, nullable=False)
    json_path = Column(Text, nullable=False)
    data_type = Column(Text, nullable=False)
    unit = Column(Text, nullable=True)
    precision = Column(Integer, nullable=True)
    is_primary = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    scale_factor = Column(Float, default=1.0)

    def as_dict(self):
        return {
            "dict_id": self.dict_id,
            "device_type_id": self.device_type_id,
            "field_name": self.field_name,
            "json_path": self.json_path,
            "data_type": self.data_type,
            "unit": self.unit,
            "precision": self.precision,
            "is_primary": self.is_primary,
            "description": self.description,
            "scale_factor": self.scale_factor,
        }

class DeviceTypeThreshold(Base):
    __tablename__ = "device_type_thresholds"
    __table_args__ = {"schema": "analytics"}

    device_type_id = Column(Integer, primary_key=True)
    battery_field = Column(Text, nullable=False)
    battery_unit = Column(Text, nullable=True)
    nominal_level = Column(Float, nullable=False)
    critical_level = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    def as_dict(self):
        return {
            "device_type_id": self.device_type_id,
            "battery_field": self.battery_field,
            "battery_unit": self.battery_unit,
            "nominal_level": self.nominal_level,
            "critical_level": self.critical_level,
            "description": self.description,
        }

class AlertDefinition(Base):
    __tablename__ = "alert_definitions"
    __table_args__ = {"schema": "analytics"}

    alert_id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("analytics.aggregation_patterns.pattern_id"), nullable=True)
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(Text, nullable=False)  # '<', '>', '<=', '>=', '=', '!='
    alert_type = Column(Text, nullable=False)
    severity = Column(Text, default="warning")  # warning, critical
    target_scope = Column(Text, default="device")  # device, room, site
    is_enabled = Column(Boolean, default=True)

    # Relationships
    pattern = relationship("AggregationPattern", back_populates="alert_definitions")

    def as_dict(self):
        return {
            "alert_id": self.alert_id,
            "pattern_id": self.pattern_id,
            "threshold_value": self.threshold_value,
            "comparison_operator": self.comparison_operator,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "target_scope": self.target_scope,
            "is_enabled": self.is_enabled,
        }

class OccupancySensor(Base):
    __tablename__ = "occupancy_sensors"
    __table_args__ = {"schema": "analytics"}

    deveui = Column(Text, primary_key=True)
    location_id = Column(UUID, nullable=True)
    is_standalone = Column(Boolean, default=False)
    group_id = Column(Text, nullable=True)
    weight = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)

    def as_dict(self):
        return {
            "deveui": self.deveui,
            "location_id": str(self.location_id) if self.location_id else None,
            "is_standalone": self.is_standalone,
            "group_id": self.group_id,
            "weight": self.weight,
            "notes": self.notes,
        }

# ═══════════════════════════════════════════════════════════════════
# ANALYTICS VIEWS (Read-only models)
# ═══════════════════════════════════════════════════════════════════

class EnrichedUplinksWithContext(Base):
    __tablename__ = "enriched_uplinks_with_context"
    __table_args__ = {"schema": "analytics"}

    uplink_uuid = Column(UUID, primary_key=True)
    deveui = Column(String(16))
    timestamp = Column(TIMESTAMP)
    device_type_id = Column(Integer)
    payload_decoded = Column(JSONB)
    uplink_metadata = Column(JSONB)
    source = Column(String(100))
    gateway_eui = Column(String(32))
    device_name = Column(String(255))
    context_device_type_id = Column(Integer)
    site_id = Column(UUID)
    floor_id = Column(UUID)
    room_id = Column(UUID)
    zone_id = Column(UUID)
    assigned_at = Column(TIMESTAMP)
    unassigned_at = Column(TIMESTAMP)

class PeopleCountingHourly(Base):
    __tablename__ = "people_counting_hourly"
    __table_args__ = {"schema": "analytics"}

    deveui = Column(Text, primary_key=True)
    hour_bucket = Column(TIMESTAMP, primary_key=True)
    daily_anchor = Column(TIMESTAMP)
    sum_in = Column(Integer)
    sum_out = Column(Integer)
    occupancy = Column(Integer)

# ═══════════════════════════════════════════════════════════════════
# NEW: ENVIRONMENTAL ANALYTICS MATERIALIZED VIEWS
# ═══════════════════════════════════════════════════════════════════

class EnvironmentalHourly(Base):
    __tablename__ = "environmental_hourly"
    __table_args__ = {"schema": "analytics"}

    deveui = Column(Text, primary_key=True)
    hour_bucket = Column(TIMESTAMP, primary_key=True)
    site_id = Column(UUID)
    floor_id = Column(UUID)
    room_id = Column(UUID)
    zone_id = Column(UUID)
    device_name = Column(Text)
    device_type = Column(Text)
    device_type_id = Column(Integer)
    
    # Temperature aggregations (data-dictionary driven)
    avg_temperature = Column(Float)
    min_temperature = Column(Float)
    max_temperature = Column(Float)
    temperature_unit = Column(Text)
    
    # Humidity aggregations
    avg_humidity = Column(Float)
    min_humidity = Column(Float)
    max_humidity = Column(Float)
    humidity_unit = Column(Text)
    
    # CO2 aggregations (only available on some sensors)
    avg_co2_ppm = Column(Float)
    min_co2_ppm = Column(Float)
    max_co2_ppm = Column(Float)
    co2_unit = Column(Text)
    
    # Metadata
    reading_count = Column(Integer)
    first_reading_time = Column(TIMESTAMP)
    last_reading_time = Column(TIMESTAMP)

    def as_dict(self):
        return {
            "deveui": self.deveui,
            "hour_bucket": self.hour_bucket.isoformat() if self.hour_bucket else None,
            "site_id": str(self.site_id) if self.site_id else None,
            "floor_id": str(self.floor_id) if self.floor_id else None,
            "room_id": str(self.room_id) if self.room_id else None,
            "zone_id": str(self.zone_id) if self.zone_id else None,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "device_type_id": self.device_type_id,
            "temperature": {
                "avg": float(self.avg_temperature) if self.avg_temperature else None,
                "min": float(self.min_temperature) if self.min_temperature else None,
                "max": float(self.max_temperature) if self.max_temperature else None,
                "unit": self.temperature_unit
            },
            "humidity": {
                "avg": float(self.avg_humidity) if self.avg_humidity else None,
                "min": float(self.min_humidity) if self.min_humidity else None,
                "max": float(self.max_humidity) if self.max_humidity else None,
                "unit": self.humidity_unit
            },
            "co2": {
                "avg": float(self.avg_co2_ppm) if self.avg_co2_ppm else None,
                "min": float(self.min_co2_ppm) if self.min_co2_ppm else None,
                "max": float(self.max_co2_ppm) if self.max_co2_ppm else None,
                "unit": self.co2_unit
            },
            "metadata": {
                "reading_count": self.reading_count,
                "first_reading_time": self.first_reading_time.isoformat() if self.first_reading_time else None,
                "last_reading_time": self.last_reading_time.isoformat() if self.last_reading_time else None
            }
        }

class EnvironmentalLatest(Base):
    __tablename__ = "environmental_latest"
    __table_args__ = {"schema": "analytics"}

    deveui = Column(Text, primary_key=True)
    timestamp = Column(TIMESTAMP)
    site_id = Column(UUID)
    floor_id = Column(UUID)
    room_id = Column(UUID)
    zone_id = Column(UUID)
    device_name = Column(Text)
    device_type = Column(Text)
    device_type_id = Column(Integer)
    
    # Environmental readings (data-dictionary normalized)
    temperature = Column(Float)
    temperature_unit = Column(Text)
    humidity = Column(Float)
    humidity_unit = Column(Text)
    co2_ppm = Column(Float)
    co2_unit = Column(Text)
    
    # Status and freshness
    environmental_status = Column(Text)  # 'ok', 'sensor_error', 'stale_data'
    minutes_since_reading = Column(Float)

    def as_dict(self):
        return {
            "deveui": self.deveui,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "site_id": str(self.site_id) if self.site_id else None,
            "floor_id": str(self.floor_id) if self.floor_id else None,
            "room_id": str(self.room_id) if self.room_id else None,
            "zone_id": str(self.zone_id) if self.zone_id else None,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "device_type_id": self.device_type_id,
            "temperature": {
                "value": float(self.temperature) if self.temperature else None,
                "unit": self.temperature_unit
            },
            "humidity": {
                "value": float(self.humidity) if self.humidity else None,
                "unit": self.humidity_unit
            },
            "co2": {
                "value": float(self.co2_ppm) if self.co2_ppm else None,
                "unit": self.co2_unit
            },
            "status": {
                "environmental_status": self.environmental_status,
                "minutes_since_reading": float(self.minutes_since_reading) if self.minutes_since_reading else None,
                "data_freshness": "fresh" if self.minutes_since_reading and self.minutes_since_reading < 60 else "stale"
            }
        }

class DeviceHealthLatest(Base):
    __tablename__ = "device_health_latest"
    __table_args__ = {"schema": "analytics"}

    deveui = Column(Text, primary_key=True)
    timestamp = Column(TIMESTAMP)
    site_id = Column(UUID)
    floor_id = Column(UUID)
    room_id = Column(UUID)
    zone_id = Column(UUID)
    device_name = Column(Text)
    device_type = Column(Text)
    device_type_id = Column(Integer)
    
    # Battery health (using threshold pattern)
    battery_level = Column(Float)
    battery_metric = Column(Text)  # 'battery_voltage' or 'battery_pct'
    battery_unit = Column(Text)
    nominal_level = Column(Float)
    critical_level = Column(Float)
    
    # Health status indicators
    battery_status = Column(Text)  # 'good', 'low', 'critical'
    connectivity_status = Column(Text)  # 'online', 'delayed', 'stale'
    overall_health = Column(Text)  # 'healthy', 'warning', 'critical', 'offline'
    minutes_since_reading = Column(Float)

    def as_dict(self):
        return {
            "deveui": self.deveui,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "site_id": str(self.site_id) if self.site_id else None,
            "floor_id": str(self.floor_id) if self.floor_id else None,
            "room_id": str(self.room_id) if self.room_id else None,
            "zone_id": str(self.zone_id) if self.zone_id else None,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "device_type_id": self.device_type_id,
            "battery": {
                "level": float(self.battery_level) if self.battery_level else None,
                "metric": self.battery_metric,
                "unit": self.battery_unit,
                "nominal_level": float(self.nominal_level) if self.nominal_level else None,
                "critical_level": float(self.critical_level) if self.critical_level else None,
                "status": self.battery_status
            },
            "connectivity": {
                "status": self.connectivity_status,
                "minutes_since_reading": float(self.minutes_since_reading) if self.minutes_since_reading else None
            },
            "overall_health": self.overall_health
        }
