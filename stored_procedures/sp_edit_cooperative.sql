-- Stored Procedure: Edit/Update Cooperative
-- Description: Updates cooperative record and all related data across 5 tables

DROP FUNCTION IF EXISTS sp_edit_cooperative(
    INTEGER, VARCHAR, INTEGER, VARCHAR, VARCHAR,
    VARCHAR, VARCHAR, VARCHAR, VARCHAR, DATE, BOOLEAN, DATE, VARCHAR, VARCHAR,
    INTEGER, INTEGER, BOOLEAN, BOOLEAN, BYTEA, BYTEA,
    NUMERIC, NUMERIC, NUMERIC, INTEGER, BYTEA,
    JSON, JSON
);

CREATE OR REPLACE FUNCTION sp_edit_cooperative(
    -- Primary key
    p_coop_id INTEGER,
    
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
    
    -- Officers data (JSON array) - will replace existing
    p_officers JSON,
    
    -- Members data (JSON array) - will replace existing
    p_members JSON
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_officer RECORD;
    v_member RECORD;
    v_profile_exists BOOLEAN;
    v_financial_exists BOOLEAN;
BEGIN
    -- Check if cooperative exists
    IF NOT EXISTS (SELECT 1 FROM cooperatives WHERE cooperatives.coop_id = p_coop_id) THEN
        RETURN QUERY SELECT FALSE, 'Cooperative not found';
        RETURN;
    END IF;
    
    -- Update cooperatives table
    UPDATE cooperatives SET
        cooperative_name = p_cooperative_name,
        staff_id = p_staff_id,
        category = p_category,
        district = p_district,
        updated_at = NOW()
    WHERE cooperatives.coop_id = p_coop_id;
    
    -- Check if profile exists
    SELECT EXISTS(SELECT 1 FROM profile_data WHERE profile_data.coop_id = p_coop_id) 
    INTO v_profile_exists;
    
    IF v_profile_exists THEN
        -- Update existing profile
        UPDATE profile_data SET
            address = p_address,
            mobile_number = p_mobile_number,
            email_address = p_email_address,
            cda_registration_number = p_cda_registration_number,
            cda_registration_date = p_cda_registration_date,
            lccdc_membership = p_lccdc_membership,
            lccdc_membership_date = p_lccdc_membership_date,
            operation_area = p_operation_area,
            business_activity = p_business_activity,
            board_of_directors_count = p_board_of_directors_count,
            salaried_employees_count = p_salaried_employees_count,
            coc_renewal = p_coc_renewal,
            cote_renewal = p_cote_renewal,
            coc_attachment = COALESCE(p_coc_attachment, coc_attachment),
            cote_attachment = COALESCE(p_cote_attachment, cote_attachment),
            updated_at = NOW()
        WHERE profile_data.coop_id = p_coop_id;
    ELSE
        -- Insert new profile
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
            p_coop_id, p_address, p_mobile_number, p_email_address,
            p_cda_registration_number, p_cda_registration_date,
            p_lccdc_membership, p_lccdc_membership_date,
            p_operation_area, p_business_activity,
            p_board_of_directors_count, p_salaried_employees_count,
            p_coc_renewal, p_cote_renewal,
            p_coc_attachment, p_cote_attachment,
            'pending'
        );
    END IF;
    
    -- Check if financial data exists for the given year
    SELECT EXISTS(
        SELECT 1 FROM financial_data 
        WHERE financial_data.coop_id = p_coop_id 
        AND report_year = p_report_year
    ) INTO v_financial_exists;
    
    IF v_financial_exists THEN
        -- Update existing financial data
        UPDATE financial_data SET
            assets = p_assets,
            paid_up_capital = p_paid_up_capital,
            net_surplus = p_net_surplus,
            attachments = COALESCE(p_financial_attachments, attachments),
            updated_at = NOW()
        WHERE financial_data.coop_id = p_coop_id 
        AND report_year = p_report_year;
    ELSE
        -- Insert new financial data
        IF p_assets IS NOT NULL OR p_paid_up_capital IS NOT NULL OR p_net_surplus IS NOT NULL THEN
            INSERT INTO financial_data (
                coop_id, assets, paid_up_capital, net_surplus,
                report_year, attachments, approval_status
            ) VALUES (
                p_coop_id, p_assets, p_paid_up_capital, p_net_surplus,
                p_report_year, p_financial_attachments, 'pending'
            );
        END IF;
    END IF;
    
    -- Replace officers (delete old, insert new)
    IF p_officers IS NOT NULL THEN
        DELETE FROM officers WHERE officers.coop_id = p_coop_id;
        
        FOR v_officer IN SELECT * FROM json_to_recordset(p_officers) AS x(
            fullname VARCHAR, position VARCHAR, gender VARCHAR, 
            mobile_number VARCHAR, email VARCHAR, user_id INTEGER
        )
        LOOP
            INSERT INTO officers (
                coop_id, fullname, position, gender, mobile_number, email, user_id
            ) VALUES (
                p_coop_id, v_officer.fullname, v_officer.position, 
                v_officer.gender::gender_enum, v_officer.mobile_number, 
                v_officer.email, v_officer.user_id
            );
        END LOOP;
    END IF;
    
    -- Replace members (delete old, insert new)
    IF p_members IS NOT NULL THEN
        DELETE FROM members WHERE members.coop_id = p_coop_id;
        
        FOR v_member IN SELECT * FROM json_to_recordset(p_members) AS x(
            fullname VARCHAR, gender VARCHAR
        )
        LOOP
            INSERT INTO members (
                coop_id, fullname, gender
            ) VALUES (
                p_coop_id, v_member.fullname, v_member.gender::gender_enum
            );
        END LOOP;
    END IF;
    
    RETURN QUERY SELECT TRUE, 'Cooperative updated successfully';
    
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT FALSE, SQLERRM;
END;
$$ LANGUAGE plpgsql;
