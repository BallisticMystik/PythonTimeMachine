-- Create a new session table with the updated schema
CREATE TABLE session_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    instrument_id VARCHAR(50),
    instrument_name VARCHAR(100),
    instrument_type VARCHAR(50),
    amount FLOAT,
    mark_price FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_percentage FLOAT,
    leverage INTEGER,
    stoploss FLOAT,
    ticker VARCHAR(20),
    timeframe VARCHAR(20),
    active BOOLEAN DEFAULT 1,
    position VARCHAR(10),
    immediate_entry BOOLEAN DEFAULT 0,
    task_id VARCHAR(36)
);

-- Copy data from the old table to the new one
INSERT INTO session_new SELECT id, user_id, instrument_id, instrument_name, instrument_type, amount, mark_price, created_at, updated_at, account_percentage, leverage, stoploss, ticker, timeframe, active, position, immediate_entry, NULL FROM session;

-- Delete the old table
DROP TABLE session;

-- Rename the new table to the original name
ALTER TABLE session_new RENAME TO session;

-- No changes needed for the user table

-- Rename the new table to the original name
ALTER TABLE user_new RENAME TO user;