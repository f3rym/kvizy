-- Add whitelist table
CREATE TABLE IF NOT EXISTS whitelist (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    added_by INTEGER REFERENCES users(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Add index for fast lookup
CREATE INDEX IF NOT EXISTS idx_whitelist_telegram_id ON whitelist(telegram_id);

-- Add whitelist_enabled flag to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_whitelisted BOOLEAN DEFAULT FALSE;

-- Mark existing users as whitelisted
UPDATE users SET is_whitelisted = TRUE;
