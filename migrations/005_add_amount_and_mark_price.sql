-- Add amount and mark_price columns to the session table
ALTER TABLE session ADD COLUMN amount FLOAT;
ALTER TABLE session ADD COLUMN mark_price FLOAT;