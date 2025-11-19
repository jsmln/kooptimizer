-- Stored Procedure: Display Cooperatives with All Related Data
-- Description: Retrieves complete cooperative records with JOINs across all 5 tables

DROP FUNCTION IF EXISTS sp_display_cooperatives(INTEGER);

CREATE OR REPLACE FUNCTION sp_display_cooperatives(
    p_coop_id INTEGER DEFAULT NULL
)
RETURNS TABLE(
    -- Cooperatives table fields
    coop_id INTEGER,
    cooperative_name VARCHAR,
    staff_id INTEGER,
    category VARCHAR,
    district VARCHAR,
    coop_created_at TIMESTAMP WITH TIME ZONE,
    coop_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Profile data fields
    profile_id INTEGER,
    address VARCHAR,
    mobile_number VARCHAR,
    email_address VARCHAR,
    cda_registration_number VARCHAR,
    cda_registration_date DATE,
    lccdc_membership BOOLEAN,
    lccdc_membership_date DATE,
    operation_area VARCHAR,
    business_activity VARCHAR,
    board_of_directors_count INTEGER,
    salaried_employees_count INTEGER,
    coc_renewal BOOLEAN,
    cote_renewal BOOLEAN,
    profile_approval_status approval_status_enum,
    profile_created_at TIMESTAMP WITH TIME ZONE,
    profile_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Financial data fields (latest year)
    financial_id INTEGER,
    assets NUMERIC,
    paid_up_capital NUMERIC,
    net_surplus NUMERIC,
    report_year INTEGER,
    financial_approval_status approval_status_enum,
    financial_created_at TIMESTAMP WITH TIME ZONE,
    financial_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Aggregated counts
    officers_count INTEGER,
    members_count INTEGER,
    
    -- Officers data (JSON array)
    officers JSON,
    
    -- Members data (JSON array)
    members JSON
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        -- Cooperatives table
        c.coop_id,
        c.cooperative_name,
        c.staff_id,
        c.category,
        c.district,
        c.created_at AS coop_created_at,
        c.updated_at AS coop_updated_at,
        
        -- Profile data
        pd.profile_id,
        pd.address,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.lccdc_membership,
        pd.lccdc_membership_date,
        pd.operation_area,
        pd.business_activity,
        pd.board_of_directors_count,
        pd.salaried_employees_count,
        pd.coc_renewal,
        pd.cote_renewal,
        pd.approval_status AS profile_approval_status,
        pd.created_at AS profile_created_at,
        pd.updated_at AS profile_updated_at,
        
        -- Financial data (latest year)
        fd.financial_id,
        fd.assets,
        fd.paid_up_capital,
        fd.net_surplus,
        fd.report_year,
        fd.approval_status AS financial_approval_status,
        fd.created_at AS financial_created_at,
        fd.updated_at AS financial_updated_at,
        
        -- Counts
        COALESCE(officer_counts.count, 0)::INTEGER AS officers_count,
        COALESCE(member_counts.count, 0)::INTEGER AS members_count,
        
        -- Officers JSON array
        COALESCE(officers_agg.officers_json, '[]'::JSON) AS officers,
        
        -- Members JSON array
        COALESCE(members_agg.members_json, '[]'::JSON) AS members
        
    FROM cooperatives c
    
    -- LEFT JOIN profile_data
    LEFT JOIN profile_data pd ON c.coop_id = pd.coop_id
    
    -- LEFT JOIN financial_data (get latest year only)
    LEFT JOIN LATERAL (
        SELECT financial_id, assets, paid_up_capital, net_surplus, 
               report_year, approval_status, created_at, updated_at
        FROM financial_data
        WHERE financial_data.coop_id = c.coop_id
        ORDER BY report_year DESC NULLS LAST, financial_id DESC
        LIMIT 1
    ) fd ON TRUE
    
    -- LEFT JOIN for officer counts
    LEFT JOIN (
        SELECT coop_id, COUNT(*) AS count
        FROM officers
        GROUP BY coop_id
    ) officer_counts ON c.coop_id = officer_counts.coop_id
    
    -- LEFT JOIN for member counts
    LEFT JOIN (
        SELECT coop_id, COUNT(*) AS count
        FROM members
        GROUP BY coop_id
    ) member_counts ON c.coop_id = member_counts.coop_id
    
    -- LEFT JOIN for officers aggregation
    LEFT JOIN (
        SELECT 
            coop_id,
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'officer_id', officer_id,
                    'user_id', user_id,
                    'fullname', fullname,
                    'position', position,
                    'gender', gender,
                    'mobile_number', mobile_number,
                    'email', email,
                    'created_at', created_at,
                    'updated_at', updated_at
                )
                ORDER BY officer_id
            ) AS officers_json
        FROM officers
        GROUP BY coop_id
    ) officers_agg ON c.coop_id = officers_agg.coop_id
    
    -- LEFT JOIN for members aggregation
    LEFT JOIN (
        SELECT 
            coop_id,
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'member_id', member_id,
                    'fullname', fullname,
                    'gender', gender,
                    'created_at', created_at
                )
                ORDER BY member_id
            ) AS members_json
        FROM members
        GROUP BY coop_id
    ) members_agg ON c.coop_id = members_agg.coop_id
    
    WHERE 
        (p_coop_id IS NULL OR c.coop_id = p_coop_id)
    
    ORDER BY c.cooperative_name;
    
END;
$$ LANGUAGE plpgsql;
