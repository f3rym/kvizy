-- Add base_url and model columns to api_keys table
ALTER TABLE api_keys
ADD COLUMN IF NOT EXISTS base_url TEXT,
ADD COLUMN IF NOT EXISTS model TEXT DEFAULT 'claude-sonnet-4-6';

-- Update existing rows to have default model
UPDATE api_keys SET model = 'claude-sonnet-4-6' WHERE model IS NULL;
