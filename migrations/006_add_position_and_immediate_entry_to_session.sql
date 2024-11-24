-- Add position and immediate_entry columns to the session table
ALTER TABLE session ADD COLUMN position VARCHAR(10);
ALTER TABLE session ADD COLUMN immediate_entry BOOLEAN DEFAULT 0;