-- Migration: Add key sharing functionality
-- Allows users to share their API keys with other users

CREATE TABLE IF NOT EXISTS key_sharing (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(owner_user_id, shared_with_user_id)
);

CREATE INDEX idx_key_sharing_owner ON key_sharing(owner_user_id);
CREATE INDEX idx_key_sharing_shared_with ON key_sharing(shared_with_user_id);

COMMENT ON TABLE key_sharing IS 'Tracks which users have access to whose API keys';
COMMENT ON COLUMN key_sharing.owner_user_id IS 'User who owns the API key';
COMMENT ON COLUMN key_sharing.shared_with_user_id IS 'User who has access to the key';
