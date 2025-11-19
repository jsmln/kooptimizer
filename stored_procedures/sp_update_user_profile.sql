-- Stored Procedure: sp_update_user_profile
-- Updates an existing user profile

CREATE OR REPLACE PROCEDURE public.sp_update_user_profile(
    IN p_user_id integer,
    IN p_fullname character varying,
    IN p_email character varying,
    IN p_mobile_number character varying,
    IN p_gender character varying,  -- Changed from gender_enum to accept string
    IN p_position character varying,
    IN p_officer_coop_id integer DEFAULT NULL,
    IN p_staff_coop_ids integer[] DEFAULT NULL
)
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_role user_role_enum;
    v_staff_id INTEGER;
    v_gender_enum gender_enum;
BEGIN
    -- Cast string gender to enum
    v_gender_enum := CASE 
        WHEN p_gender IS NOT NULL THEN p_gender::gender_enum 
        ELSE NULL 
    END;

    -- Get the user's role
    SELECT role INTO v_role FROM users WHERE user_id = p_user_id;

    -- Update the username (email)
    UPDATE users SET username = p_email, updated_at = NOW() WHERE user_id = p_user_id;

    -- Update the specific profile
    IF v_role = 'admin'::user_role_enum THEN
        UPDATE admin
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position
        WHERE user_id = p_user_id;
        
    ELSIF v_role = 'staff'::user_role_enum THEN
        UPDATE staff
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position
        WHERE user_id = p_user_id
        RETURNING staff_id INTO v_staff_id;
        
        -- Un-assign all current coops from this staff
        UPDATE cooperatives SET staff_id = NULL WHERE staff_id = v_staff_id;
        
        -- Re-assign the new list of coops
        IF p_staff_coop_ids IS NOT NULL AND array_length(p_staff_coop_ids, 1) > 0 THEN
            UPDATE cooperatives
            SET staff_id = v_staff_id
            WHERE coop_id = ANY(p_staff_coop_ids);
        END IF;

    ELSIF v_role = 'officer'::user_role_enum THEN
        UPDATE officers
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position, 
            coop_id = p_officer_coop_id
        WHERE user_id = p_user_id;
    END IF;

END;
$procedure$;
