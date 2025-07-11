CREATE TABLE uplinks (
    id SERIAL PRIMARY KEY,
    deveui TEXT NOT NULL,
    received_at TIMESTAMPTZ DEFAULT now(),
    raw_payload JSONB
);
