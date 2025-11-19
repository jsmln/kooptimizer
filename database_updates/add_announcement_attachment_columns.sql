-- Add attachment metadata columns to announcements table
-- Run this SQL in your PostgreSQL database (kooptimizer)

ALTER TABLE announcements 
ADD COLUMN IF NOT EXISTS attachment_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS attachment_content_type VARCHAR(255),
ADD COLUMN IF NOT EXISTS attachment_size BIGINT;

-- Verify the columns were added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'announcements' 
AND column_name LIKE 'attachment%'
ORDER BY column_name;
