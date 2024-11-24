-- Add instrument_name and instrument_type columns if they don't exist
ALTER TABLE session ADD COLUMN instrument_name VARCHAR(100);
ALTER TABLE session ADD COLUMN instrument_type VARCHAR(50);