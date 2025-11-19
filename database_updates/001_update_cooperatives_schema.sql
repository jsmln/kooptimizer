-- Migration: Update cooperatives table schema
-- Date: 2025-11-20
-- Description: Add category and district columns, remove mobile_number column

BEGIN;

-- Add new columns to cooperatives table
ALTER TABLE cooperatives 
ADD COLUMN IF NOT EXISTS category VARCHAR(100),
ADD COLUMN IF NOT EXISTS district VARCHAR(100);

-- Create index for faster category and district lookups
CREATE INDEX IF NOT EXISTS idx_cooperatives_category ON cooperatives(category);
CREATE INDEX IF NOT EXISTS idx_cooperatives_district ON cooperatives(district);

-- Remove mobile_number column (data now stored in profile_data table)
ALTER TABLE cooperatives 
DROP COLUMN IF EXISTS mobile_number;

-- Add comment for documentation
COMMENT ON COLUMN cooperatives.category IS 'Type of cooperative: Credit, Service, Marketing, etc.';
COMMENT ON COLUMN cooperatives.district IS 'Geographical district/zone of the cooperative';

COMMIT;
