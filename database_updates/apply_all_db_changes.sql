-- ============================================
-- MASTER SCRIPT: Apply All Database Changes
-- Data Bank Management System - OCR Integration
-- Date: 2025-11-20
-- ============================================

-- This script applies all necessary database schema changes and stored procedures
-- for the Data Bank Management System with OCR Assistant integration.

BEGIN;

-- ============================================
-- STEP 1: Schema Migration
-- ============================================

-- Add new columns to cooperatives table
ALTER TABLE cooperatives 
ADD COLUMN IF NOT EXISTS category VARCHAR(100),
ADD COLUMN IF NOT EXISTS district VARCHAR(100);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_cooperatives_category ON cooperatives(category);
CREATE INDEX IF NOT EXISTS idx_cooperatives_district ON cooperatives(district);

-- Remove mobile_number column (data now stored in profile_data table)
ALTER TABLE cooperatives 
DROP COLUMN IF EXISTS mobile_number;

-- Add comments for documentation
COMMENT ON COLUMN cooperatives.category IS 'Type of cooperative: Credit, Service, Marketing, etc.';
COMMENT ON COLUMN cooperatives.district IS 'Geographical district/zone of the cooperative';

-- ============================================
-- STEP 2: Create Stored Procedures
-- ============================================

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS sp_add_cooperative(VARCHAR, INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, DATE, BOOLEAN, DATE, VARCHAR, VARCHAR, INTEGER, INTEGER, BOOLEAN, BOOLEAN, BYTEA, BYTEA, NUMERIC, NUMERIC, NUMERIC, INTEGER, BYTEA, JSON, JSON);
DROP FUNCTION IF EXISTS sp_display_cooperatives(INTEGER);
DROP FUNCTION IF EXISTS sp_edit_cooperative(INTEGER, VARCHAR, INTEGER, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, DATE, BOOLEAN, DATE, VARCHAR, VARCHAR, INTEGER, INTEGER, BOOLEAN, BOOLEAN, BYTEA, BYTEA, NUMERIC, NUMERIC, NUMERIC, INTEGER, BYTEA, JSON, JSON);
DROP FUNCTION IF EXISTS sp_delete_cooperative(INTEGER, BOOLEAN);

COMMIT;

-- ============================================
-- INSTRUCTIONS FOR MANUAL EXECUTION
-- ============================================

-- After running this migration script, execute the following stored procedure files:
-- 1. stored_procedures/sp_add_cooperative.sql
-- 2. stored_procedures/sp_display_cooperatives.sql
-- 3. stored_procedures/sp_edit_cooperative.sql
-- 4. stored_procedures/sp_delete_cooperative.sql

-- To execute in psql:
-- \i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_add_cooperative.sql
-- \i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_display_cooperatives.sql
-- \i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_edit_cooperative.sql
-- \i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_delete_cooperative.sql

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify schema changes
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cooperatives' ORDER BY ordinal_position;

-- Test the stored procedures
-- SELECT * FROM sp_display_cooperatives();
-- SELECT * FROM sp_display_cooperatives(1);
