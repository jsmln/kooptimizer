-- ============================================
-- STORED PROCEDURES QUICK REFERENCE GUIDE
-- ============================================

-- ============================================
-- 1. ADD COOPERATIVE
-- ============================================

SELECT * FROM sp_add_cooperative(
    -- Cooperatives table (4 params)
    'New Cooperative Name',              -- p_cooperative_name
    1,                                   -- p_staff_id (nullable)
    'Credit',                            -- p_category (Credit, Service, Marketing, etc.)
    'District 1',                        -- p_district
    
    -- Profile data (16 params)
    'Lipa City, Batangas',              -- p_address
    '09171234567',                       -- p_mobile_number
    'coop@example.com',                  -- p_email_address
    '1414-12345678',                     -- p_cda_registration_number
    '2020-01-15',                        -- p_cda_registration_date
    TRUE,                                -- p_lccdc_membership
    '2021-06-01',                        -- p_lccdc_membership_date
    'Lipa City',                         -- p_operation_area
    'Savings and Credit',                -- p_business_activity
    7,                                   -- p_board_of_directors_count
    3,                                   -- p_salaried_employees_count
    TRUE,                                -- p_coc_renewal
    TRUE,                                -- p_cote_renewal
    NULL,                                -- p_coc_attachment (bytea)
    NULL,                                -- p_cote_attachment (bytea)
    
    -- Financial data (5 params)
    500000.00,                           -- p_assets
    250000.00,                           -- p_paid_up_capital
    50000.00,                            -- p_net_surplus
    2024,                                -- p_report_year
    NULL,                                -- p_financial_attachments (bytea)
    
    -- Officers (JSON array)
    '[
        {
            "fullname": "Juan Dela Cruz",
            "position": "Chairperson",
            "gender": "male",
            "mobile_number": "09171111111",
            "email": "juan@example.com",
            "user_id": null
        },
        {
            "fullname": "Maria Santos",
            "position": "Treasurer",
            "gender": "female",
            "mobile_number": "09172222222",
            "email": "maria@example.com",
            "user_id": null
        }
    ]'::JSON,
    
    -- Members (JSON array)
    '[
        {
            "fullname": "Pedro Reyes",
            "gender": "male"
        },
        {
            "fullname": "Ana Lopez",
            "gender": "female"
        }
    ]'::JSON
);

-- ============================================
-- 2. DISPLAY COOPERATIVES
-- ============================================

-- Get all cooperatives with full details
SELECT * FROM sp_display_cooperatives();

-- Get specific cooperative by ID
SELECT * FROM sp_display_cooperatives(1);

-- Example: Filter by category in your application
SELECT * FROM sp_display_cooperatives() 
WHERE category = 'Credit';

-- Example: Filter by district
SELECT * FROM sp_display_cooperatives() 
WHERE district = 'District 1';

-- ============================================
-- 3. EDIT COOPERATIVE
-- ============================================

SELECT * FROM sp_edit_cooperative(
    -- Primary key (1 param)
    1,                                   -- p_coop_id
    
    -- Cooperatives table (4 params)
    'Updated Cooperative Name',          -- p_cooperative_name
    1,                                   -- p_staff_id
    'Service',                           -- p_category (updated)
    'District 2',                        -- p_district (updated)
    
    -- Profile data (16 params)
    'Updated Address, Lipa City',        -- p_address
    '09179999999',                       -- p_mobile_number
    'updated@example.com',               -- p_email_address
    '1414-12345678',                     -- p_cda_registration_number
    '2020-01-15',                        -- p_cda_registration_date
    TRUE,                                -- p_lccdc_membership
    '2021-06-01',                        -- p_lccdc_membership_date
    'Lipa City',                         -- p_operation_area
    'Updated Business Activity',         -- p_business_activity
    9,                                   -- p_board_of_directors_count (updated)
    5,                                   -- p_salaried_employees_count (updated)
    TRUE,                                -- p_coc_renewal
    TRUE,                                -- p_cote_renewal
    NULL,                                -- p_coc_attachment (NULL = keep existing)
    NULL,                                -- p_cote_attachment (NULL = keep existing)
    
    -- Financial data (5 params)
    750000.00,                           -- p_assets (updated)
    350000.00,                           -- p_paid_up_capital (updated)
    75000.00,                            -- p_net_surplus (updated)
    2024,                                -- p_report_year
    NULL,                                -- p_financial_attachments (NULL = keep existing)
    
    -- Officers (JSON array - replaces all existing)
    '[
        {
            "fullname": "Juan Dela Cruz",
            "position": "Chairperson",
            "gender": "male",
            "mobile_number": "09171111111",
            "email": "juan@example.com",
            "user_id": null
        },
        {
            "fullname": "Maria Santos",
            "position": "Treasurer",
            "gender": "female",
            "mobile_number": "09172222222",
            "email": "maria@example.com",
            "user_id": null
        },
        {
            "fullname": "New Officer",
            "position": "Secretary",
            "gender": "male",
            "mobile_number": "09173333333",
            "email": "new@example.com",
            "user_id": null
        }
    ]'::JSON,
    
    -- Members (JSON array - replaces all existing)
    '[
        {
            "fullname": "Pedro Reyes",
            "gender": "male"
        },
        {
            "fullname": "Ana Lopez",
            "gender": "female"
        },
        {
            "fullname": "New Member",
            "gender": "female"
        }
    ]'::JSON
);

-- ============================================
-- 4. DELETE COOPERATIVE
-- ============================================

-- Soft delete (mark as inactive, keep data)
SELECT * FROM sp_delete_cooperative(1, FALSE);

-- Hard delete (permanently remove all data)
SELECT * FROM sp_delete_cooperative(1, TRUE);

-- Warning: Hard delete removes:
-- - Cooperative record
-- - Profile data
-- - Financial data
-- - All officers
-- - All members
-- - Related announcement recipients

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check cooperatives schema
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'cooperatives' 
ORDER BY ordinal_position;

-- Count cooperatives by category
SELECT category, COUNT(*) as count
FROM cooperatives
GROUP BY category
ORDER BY count DESC;

-- Count cooperatives by district
SELECT district, COUNT(*) as count
FROM cooperatives
GROUP BY district
ORDER BY count DESC;

-- Get cooperatives with most officers
SELECT 
    c.cooperative_name,
    COUNT(o.officer_id) as officer_count
FROM cooperatives c
LEFT JOIN officers o ON c.coop_id = o.coop_id
GROUP BY c.coop_id, c.cooperative_name
ORDER BY officer_count DESC;

-- Get cooperatives with most members
SELECT 
    c.cooperative_name,
    COUNT(m.member_id) as member_count
FROM cooperatives c
LEFT JOIN members m ON c.coop_id = m.coop_id
GROUP BY c.coop_id, c.cooperative_name
ORDER BY member_count DESC;

-- Get financial summary by year
SELECT 
    f.report_year,
    COUNT(*) as coop_count,
    SUM(f.assets) as total_assets,
    AVG(f.assets) as avg_assets,
    SUM(f.paid_up_capital) as total_capital,
    SUM(f.net_surplus) as total_surplus
FROM financial_data f
GROUP BY f.report_year
ORDER BY f.report_year DESC;

-- ============================================
-- SAMPLE DATA CATEGORIES
-- ============================================

-- Common cooperative categories:
-- - Credit
-- - Service
-- - Marketing
-- - Consumer
-- - Producer
-- - Housing
-- - Workers
-- - Multi-purpose
-- - Agricultural
-- - Transport

-- ============================================
-- NOTES
-- ============================================

-- 1. Gender enum values: 'male', 'female', 'other'
-- 2. Approval status enum: 'pending', 'approved', 'rejected'
-- 3. All timestamps use 'Asia/Manila' timezone (UTC+8)
-- 4. Financial data is per year - multiple records possible
-- 5. Officers and members are replaced entirely on edit
-- 6. NULL values in edit keep existing data for attachments
-- 7. Profile and financial records auto-create if missing on edit
