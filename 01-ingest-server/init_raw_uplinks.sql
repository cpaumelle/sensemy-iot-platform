CREATE TABLE IF NOT EXISTS raw_uplinks (
    id SERIAL PRIMARY KEY,
    deveui TEXT NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    payload JSONB NOT NULL
);
