-- Add scan session tracking
ALTER TABLE files ADD COLUMN scan_session_id UUID DEFAULT gen_random_uuid();
ALTER TABLE directories ADD COLUMN scan_session_id UUID DEFAULT gen_random_uuid();

-- Remove any unique constraints on filepath
-- ALTER TABLE files DROP CONSTRAINT IF EXISTS files_filepath_key;

-- Create index for performance but allow duplicates
CREATE INDEX IF NOT EXISTS idx_files_filepath_session ON files(filepath, scan_session_id); 