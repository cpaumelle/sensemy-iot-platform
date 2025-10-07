-- init_analytics_db.sql
-- Version: 2025-07-16 16:31 UTC
-- Analytics DB schema - no cross-schema foreign keys

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION analytics_user;
SET search_path TO analytics, public;

CREATE TABLE IF NOT EXISTS device_context (
    deveui TEXT PRIMARY KEY,
    device_type_id INTEGER NOT NULL,
    site_id INTEGER,
    floor_id INTEGER,
    room_id INTEGER,
    zone_id INTEGER,
    last_gateway TEXT,
    firmware_version TEXT,
    battery_status TEXT,
    status TEXT,
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    last_communication TIMESTAMPTZ,
    location_confidence NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
    -- Removed FK constraints to external schemas for compatibility
);

CREATE TABLE IF NOT EXISTS processed_uplinks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deveui TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    decoded_fields JSONB,
    normalized_fields JSONB,
    network_metrics JSONB,
    device_type_id INTEGER,
    site_id INTEGER,
    zone_id INTEGER,
    inserted_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT fk_dev_ctx_deveui FOREIGN KEY (deveui) REFERENCES device_context(deveui)
    -- Removed FKs referencing device schema tables
);

CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    device_type TEXT,
    rule_name TEXT,
    condition TEXT,
    enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alert_rules(id),
    triggered_at TIMESTAMPTZ,
    status TEXT,
    details JSONB
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name TEXT,
    value DOUBLE PRECISION,
    timestamp TIMESTAMPTZ,
    tags JSONB
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_processed_uplinks_deveui ON processed_uplinks(deveui);
CREATE INDEX IF NOT EXISTS idx_processed_uplinks_timestamp ON processed_uplinks(timestamp);
CREATE INDEX IF NOT EXISTS idx_device_context_device_type ON device_context(device_type_id);
CREATE INDEX IF NOT EXISTS idx_device_context_site ON device_context(site_id);
CREATE INDEX IF NOT EXISTS idx_device_context_zone ON device_context(zone_id);

-- Optional: grant privileges if using multiple users
GRANT USAGE ON SCHEMA analytics TO analytics_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO analytics_user;
-- Done