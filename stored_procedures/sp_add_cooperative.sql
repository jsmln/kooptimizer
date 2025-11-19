-- Stored Procedure: Add New Cooperative
-- Description: Inserts a new cooperative record with all related data

DROP FUNCTION IF EXISTS sp_add_cooperative(
    VARCHAR, INTEGER, VARCHAR, VARCHAR,
    VARCHAR, VARCHAR, VARCHAR, VARCHAR, DATE, BOOLEAN, DATE, VARCHAR, VARCHAR,
    INTEGER, INTEGER, BOOLEAN, BOOLEAN, BYTEA, BYTEA,
    NUMERIC, NUMERIC, NUMERIC, INTEGER, BYTEA,
    JSON, JSON
);

CREATE OR REPLACE FUNCTION sp_add_cooperative(
    -- Cooperatives table params
    p_cooperative_name VARCHAR(200),
    p_staff_id INTEGER,
    p_category VARCHAR(100),
    p_district VARCHAR(100),
    
    -- Profile data params
    p_address VARCHAR(255),
    p_mobile_number VARCHAR(20),
    p_email_address VARCHAR(100),
    p_cda_registration_number VARCHAR(100),
    p_cda_registration_date DATE,
    p_lccdc_membership BOOLEAN,
    p_lccdc_membership_date DATE,
    p_operation_area VARCHAR(100),
    p_business_activity VARCHAR(100),
    p_board_of_directors_count INTEGER,
    p_salaried_employees_count INTEGER,
    p_coc_renewal BOOLEAN,
    p_cote_renewal BOOLEAN,
    p_coc_attachment BYTEA,
    p_cote_attachment BYTEA,
    
    -- Financial data params
    p_assets NUMERIC(20,2),
    p_paid_up_capital NUMERIC(20,2),
    p_net_surplus NUMERIC(20,2),
    p_report_year INTEGER,
    p_financial_attachments BYTEA,
    
    -- Officers data (JSON array)
    p_officers JSON,
    
    -- Members data (JSON array)
    p_members JSON
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT,
    coop_id INTEGER
) AS $$
DECLARE
    v_coop_id INTEGER;
    v_officer RECORD;
    v_member RECORD;
BEGIN
    -- Insert into cooperatives table
    INSERT INTO cooperatives (
        cooperative_name, staff_id, category, district
    ) VALUES (
        p_cooperative_name, p_staff_id, p_category, p_district
    ) RETURNING cooperatives.coop_id INTO v_coop_id;
    
    -- Insert into profile_data table
    INSERT INTO profile_data (
        coop_id, address, mobile_number, email_address,
        cda_registration_number, cda_registration_date,
        lccdc_membership, lccdc_membership_date,
        operation_area, business_activity,
        board_of_directors_count, salaried_employees_count,
        coc_renewal, cote_renewal,
        coc_attachment, cote_attachment,
        approval_status
    ) VALUES (
        v_coop_id, p_address, p_mobile_number, p_email_address,
        p_cda_registration_number, p_cda_registration_date,
        p_lccdc_membership, p_lccdc_membership_date,
        p_operation_area, p_business_activity,
        p_board_of_directors_count, p_salaried_employees_count,
        p_coc_renewal, p_cote_renewal,
        p_coc_attachment, p_cote_attachment,
        'pending'
    );
    
    -- Insert into financial_data table
    IF p_assets IS NOT NULL OR p_paid_up_capital IS NOT NULL OR p_net_surplus IS NOT NULL THEN
        INSERT INTO financial_data (
            coop_id, assets, paid_up_capital, net_surplus,
            report_year, attachments, approval_status
        ) VALUES (
            v_coop_id, p_assets, p_paid_up_capital, p_net_surplus,
            p_report_year, p_financial_attachments, 'pending'
        );
    END IF;
    
    -- Insert officers (if provided)
    IF p_officers IS NOT NULL THEN
        FOR v_officer IN SELECT * FROM json_to_recordset(p_officers) AS x(
            fullname VARCHAR, position VARCHAR, gender VARCHAR, 
            mobile_number VARCHAR, email VARCHAR, user_id INTEGER
        )
        LOOP
            INSERT INTO officers (
                coop_id, fullname, position, gender, mobile_number, email, user_id
            ) VALUES (
                v_coop_id, v_officer.fullname, v_officer.position, 
                v_officer.gender::gender_enum, v_officer.mobile_number, 
                v_officer.email, v_officer.user_id
            );
        END LOOP;
    END IF;
    
    -- Insert members (if provided)
    IF p_members IS NOT NULL THEN
        FOR v_member IN SELECT * FROM json_to_recordset(p_members) AS x(
            fullname VARCHAR, gender VARCHAR
        )
        LOOP
            INSERT INTO members (
                coop_id, fullname, gender
            ) VALUES (
                v_coop_id, v_member.fullname, v_member.gender::gender_enum
            );
        END LOOP;
    END IF;
    
    RETURN QUERY SELECT TRUE, 'Cooperative added successfully', v_coop_id;
    
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT FALSE, SQLERRM, NULL::INTEGER;
END;
$$ LANGUAGE plpgsql;
