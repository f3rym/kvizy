-- Add success column to audit_logs table

ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS success BOOLEAN DEFAULT TRUE;

-- Create index on success column for filtering
CREATE INDEX IF NOT EXISTS idx_audit_logs_success ON audit_logs(success);

-- Create index on action column for filtering
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
