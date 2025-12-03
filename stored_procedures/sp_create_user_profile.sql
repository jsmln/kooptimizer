-- Stored Procedure: sp_create_user_profile
-- Creates a new user account with appropriate role-specific profile
-- Now handles duplicate usernames gracefully

CREATE OR REPLACE FUNCTION public.sp_create_user_profile(
    p_username character varying,
    p_password_hash character varying,
    p_role character varying,  -- Changed from user_role_enum to accept string
    p_fullname character varying,
    p_email character varying,
    p_mobile_number character varying,
    p_gender character varying,  -- Changed from gender_enum to accept string
    p_position character varying,
    p_officer_coop_id integer DEFAULT NULL,
    p_staff_coop_ids integer[] DEFAULT NULL
)
RETURNS TABLE(
    new_user_id integer,
    new_profile_id integer,
    formatted_id character varying,
    user_role character varying
)
LANGUAGE plpgsql
AS $function$
DECLARE
    v_user_id INTEGER;
    v_profile_id INTEGER;
    v_formatted_id VARCHAR(10);
    v_role_enum user_role_enum;
    v_gender_enum gender_enum;
BEGIN
    -- Cast string inputs to enums
    v_role_enum := p_role::user_role_enum;
    v_gender_enum := CASE 
        WHEN p_gender IS NOT NULL THEN p_gender::gender_enum 
        ELSE NULL 
    END;

    -- Check if user already exists
    SELECT user_id INTO v_user_id FROM users WHERE username = p_username;
    
    IF v_user_id IS NOT NULL THEN
        -- User already exists, raise exception
        RAISE EXCEPTION 'USERNAME_EXISTS: User with email % already exists', p_username;
    END IF;

    -- 1. Create the user
    INSERT INTO users (username, password_hash, role)
    VALUES (p_username, p_password_hash, v_role_enum)
    RETURNING user_id INTO v_user_id;

    -- 2. Create the specific profile
    CASE v_role_enum
        WHEN 'admin'::user_role_enum THEN
            INSERT INTO admin (user_id, fullname, position, gender, mobile_number, email)
            VALUES (v_user_id, p_fullname, p_position, v_gender_enum, p_mobile_number, p_email)
            RETURNING admin_id INTO v_profile_id;

            v_formatted_id := 'A' || LPAD(v_profile_id::TEXT, 3, '0');

        WHEN 'staff'::user_role_enum THEN
            INSERT INTO staff (user_id, fullname, position, gender, mobile_number, email)
            VALUES (v_user_id, p_fullname, p_position, v_gender_enum, p_mobile_number, p_email)
            RETURNING staff_id INTO v_profile_id;

            v_formatted_id := 'S' || LPAD(v_profile_id::TEXT, 3, '0');

            -- Assign this new staff to selected cooperatives
            IF p_staff_coop_ids IS NOT NULL AND array_length(p_staff_coop_ids, 1) > 0 THEN
                UPDATE cooperatives
                SET staff_id = v_profile_id
                WHERE coop_id = ANY(p_staff_coop_ids);
            END IF;

        WHEN 'officer'::user_role_enum THEN
            INSERT INTO officers (user_id, coop_id, fullname, position, gender, mobile_number, email)
            VALUES (v_user_id, p_officer_coop_id, p_fullname, p_position, v_gender_enum, p_mobile_number, p_email)
            RETURNING officer_id INTO v_profile_id;

            v_formatted_id := 'O' || LPAD(v_profile_id::TEXT, 3, '0');
    END CASE;

    -- 3. Return the new IDs
    RETURN QUERY
    SELECT v_user_id, v_profile_id, v_formatted_id, p_role;

END;
$function$;
