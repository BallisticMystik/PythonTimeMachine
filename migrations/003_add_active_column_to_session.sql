-- Check if the 'active' column already exists
CREATE TABLE IF NOT EXISTS temp_session AS SELECT * FROM session;
DROP TABLE session;
CREATE TABLE session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    instrument_id VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_percentage FLOAT,
    leverage INTEGER,
    stoploss FLOAT,
    ticker VARCHAR(20),
    timeframe VARCHAR(20),
    active BOOLEAN DEFAULT 1
);
INSERT INTO session (
    id, user_id, instrument_id, created_at, updated_at, 
    account_percentage, leverage, stoploss, ticker, timeframe, active
)
SELECT 
    id, user_id, instrument_id, created_at, updated_at, 
    account_percentage, leverage, stoploss, ticker, timeframe, 1
FROM temp_session;
DROP TABLE temp_session;