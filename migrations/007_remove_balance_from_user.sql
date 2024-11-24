-- Create a new table without the balance column
CREATE TABLE user_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    signing_key VARCHAR(256),
    wallet_address VARCHAR(256),
    api_key VARCHAR(256),
    api_secret VARCHAR(256),
    env VARCHAR(10),
    encryption_key VARCHAR(256)
);

-- Copy data from the old table to the new one
INSERT INTO user_new SELECT id, username, email, password_hash, signing_key, wallet_address, api_key, api_secret, env, encryption_key FROM user;

-- Drop the old table
DROP TABLE user;

-- Rename the new table to the original name
ALTER TABLE user_new RENAME TO user;