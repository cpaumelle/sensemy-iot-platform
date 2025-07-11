-- Set the server-wide timezone to UTC
SET timezone TO 'UTC';

-- Modify the database to use UTC by default
ALTER DATABASE <database_name> SET timezone TO 'UTC';
