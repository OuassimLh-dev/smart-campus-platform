-- Apply once to an existing PostgreSQL database before running this version.
-- Existing users keep NULL credentials and cannot log in.
BEGIN;
ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255);
COMMIT;
