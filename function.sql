CREATE OR REPLACE FUNCTION public.armor(bytea)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_armor$function$

CREATE OR REPLACE FUNCTION public.armor(bytea, text[], text[])
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_armor$function$

CREATE OR REPLACE FUNCTION public.crypt(text, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_crypt$function$

CREATE OR REPLACE FUNCTION public.dearmor(text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_dearmor$function$

CREATE OR REPLACE FUNCTION public.decrypt(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_decrypt$function$

CREATE OR REPLACE FUNCTION public.decrypt_iv(bytea, bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_decrypt_iv$function$

CREATE OR REPLACE FUNCTION public.digest(text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_digest$function$

CREATE OR REPLACE FUNCTION public.digest(bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_digest$function$

CREATE OR REPLACE FUNCTION public.encrypt(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_encrypt$function$

CREATE OR REPLACE FUNCTION public.encrypt_iv(bytea, bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_encrypt_iv$function$

CREATE OR REPLACE FUNCTION public.fips_mode()
 RETURNS boolean
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_check_fipsmode$function$

CREATE OR REPLACE FUNCTION public.fn_trigger_set_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$

CREATE OR REPLACE FUNCTION public.gen_random_bytes(integer)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_random_bytes$function$

CREATE OR REPLACE FUNCTION public.gen_random_uuid()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE
AS '$libdir/pgcrypto', $function$pg_random_uuid$function$

CREATE OR REPLACE FUNCTION public.gen_salt(text)
 RETURNS text
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_gen_salt$function$

CREATE OR REPLACE FUNCTION public.gen_salt(text, integer)
 RETURNS text
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_gen_salt_rounds$function$

CREATE OR REPLACE FUNCTION public.hmac(text, text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_hmac$function$

CREATE OR REPLACE FUNCTION public.hmac(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pg_hmac$function$

CREATE OR REPLACE FUNCTION public.pgp_armor_headers(text, OUT key text, OUT value text)
 RETURNS SETOF record
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_armor_headers$function$

CREATE OR REPLACE FUNCTION public.pgp_key_id(bytea)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_key_id_w$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt(bytea, bytea)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt(bytea, bytea, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt(bytea, bytea, text, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_decrypt_bytea(bytea, bytea, text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_decrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt(text, bytea)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt(text, bytea, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_pub_encrypt_bytea(bytea, bytea, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_pub_encrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt(bytea, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt(bytea, text, text)
 RETURNS text
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt_bytea(bytea, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_decrypt_bytea(bytea, text, text)
 RETURNS bytea
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_decrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt(text, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt(text, text, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_text$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt_bytea(bytea, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.pgp_sym_encrypt_bytea(bytea, text, text)
 RETURNS bytea
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/pgcrypto', $function$pgp_sym_encrypt_bytea$function$

CREATE OR REPLACE FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_is_first_login boolean, p_verification_status character varying)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE users
    SET
        password_hash = p_new_password_hash,
        is_first_login = p_is_first_login,
        verification_status = p_verification_status,
        updated_at = NOW()
    WHERE
        user_id = p_user_id;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_is_first_login boolean, p_verification_status verification_status_enum)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE users
    SET
        password_hash = p_new_password_hash,
        is_first_login = p_is_first_login,
        verification_status = p_verification_status,
        updated_at = NOW()
    WHERE
        user_id = p_user_id;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_verification_status_text character varying)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE users
    SET
        password_hash = p_new_password_hash,
        
        -- THIS IS THE FIX for your error:
        -- We explicitly CAST the text from Python to the enum type
        verification_status = p_verification_status_text::verification_status_enum,
        
        updated_at = NOW()
        
        -- We NO LONGER need to set is_first_login here!
        -- The trigger will handle it automatically.
    WHERE
        user_id = p_user_id;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_get_announcements_by_status(p_status announcement_status_enum)
 RETURNS TABLE(announcement_id integer, title character varying, description text, type announcement_type_enum, status_classification announcement_status_enum, scope character varying, sent_at timestamp with time zone, created_at timestamp with time zone, updated_at timestamp with time zone, creator_name character varying)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        a.announcement_id,
        a.title,
        a.description,
        a.type,
        a.status_classification,
        a.scope,
        a.sent_at,
        a.created_at,
        a.updated_at,
        COALESCE(s.fullname, adm.fullname, 'Unknown') AS creator_name
    FROM
        announcements a
    LEFT JOIN
        staff s ON a.staff_id = s.staff_id
    LEFT JOIN
        admin adm ON a.admin_id = adm.admin_id
    WHERE
        a.status_classification = p_status
    ORDER BY
        a.updated_at DESC; -- Order by most recently updated
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_get_mobile_by_userid(p_user_id integer)
 RETURNS character varying
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_role user_role_enum;
    v_mobile_number VARCHAR(20);
BEGIN
    -- 1. Find the user's role
    SELECT role INTO v_role FROM users WHERE user_id = p_user_id;

    -- 2. Get the mobile number from the correct table based on the role
    IF v_role = 'admin' THEN
        SELECT mobile_number INTO v_mobile_number
        FROM admin WHERE user_id = p_user_id;

    ELSIF v_role = 'staff' THEN
        SELECT mobile_number INTO v_mobile_number
        FROM staff WHERE user_id = p_user_id;

    ELSIF v_role = 'officer' THEN
        -- Use LIMIT 1 to handle cases where an officer (like 'officer_kate')
        -- might have multiple officer records. We just need one mobile number.
        SELECT mobile_number INTO v_mobile_number
        FROM officers WHERE user_id = p_user_id
        LIMIT 1;
        
    END IF;

    -- 3. Return the found number
    RETURN v_mobile_number;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
    WHEN OTHERS THEN
        -- Log error or handle as needed
        RETURN NULL;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_get_sms_recipients(p_announcement_id integer)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
    phone_list TEXT;
BEGIN
    WITH all_numbers AS (
        -- Get numbers from 'coop' recipients (all officers in that coop)
        SELECT o.mobile_number
        FROM officers o
        JOIN announcement_recipients ar ON o.coop_id = ar.coop_id
        WHERE ar.announcement_id = p_announcement_id
          AND o.mobile_number IS NOT NULL
          AND o.mobile_number != ''

        UNION

        -- Get numbers from specific 'officer' recipients
        SELECT o.mobile_number
        FROM officers o
        JOIN announcement_officer_recipients aor ON o.officer_id = aor.officer_id
        WHERE aor.announcement_id = p_announcement_id
          AND o.mobile_number IS NOT NULL
          AND o.mobile_number != ''
    )
    -- Aggregate all unique numbers into a single, comma-separated string
    SELECT string_agg(DISTINCT mobile_number, ',')
    INTO phone_list
    FROM all_numbers;

    RETURN phone_list;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_login_user(p_username character varying, p_password character varying)
 RETURNS user_login_status
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_user users;
    v_is_first_login_original BOOLEAN;
    v_login_status user_login_status;
BEGIN
    -- 1. Check if username exists
    SELECT * INTO v_user FROM users WHERE username = p_username;

    IF NOT FOUND THEN
        -- User does not exist
        v_login_status := ('INVALID_USERNAME_OR_PASSWORD', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
    END IF;

    -- 2. Check if the password matches
    
    -- === THIS IS THE FIX ===
    -- OLD: IF v_user.password_hash = crypt(p_password, v_user.password_hash) THEN
    -- NEW:
    IF verify_pbkdf2_sha256(p_password, v_user.password_hash) THEN
    -- =======================
    
        -- Password is correct!

        -- 3. Get the original is_first_login status
        v_is_first_login_original := v_user.is_first_login;

        -- 4. If it was their first login, update the flag to false
        --    NOTE: Your trigger 'trg_auto_set_first_login' from before
        --    might make this redundant. This is fine, but good to be aware.
        IF v_is_first_login_original = TRUE THEN
            UPDATE users
            SET
                is_first_login = FALSE,
                updated_at = now()
            WHERE user_id = v_user.user_id;
        END IF;

        -- 5. Return a success status
        v_login_status := (
            'SUCCESS',
            v_user.user_id,
            v_user.role,
            v_user.verification_status,
            v_is_first_login_original -- Return the *original* login status
        )::user_login_status;
        
        RETURN v_login_status;
        
    ELSE
        -- Password does not match
        v_login_status := ('INVALID_USERNAME_OR_PASSWORD', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        -- Handle any other unexpected errors
        RAISE NOTICE 'An error occurred: %', SQLERRM;
        v_login_status := ('ERROR', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_register_user(p_username character varying, p_password_hash character varying, p_role user_role_enum)
 RETURNS users
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_new_user users;
BEGIN
    INSERT INTO users (username, password_hash, role, verification_status)
    VALUES (
        p_username, 
        p_password_hash, 
        p_role,  -- No cast is needed
        'pending'
    )
    RETURNING * INTO v_new_user;

    RETURN v_new_user;

EXCEPTION
    WHEN unique_violation THEN
        RETURN NULL;
END;
$function$

CREATE OR REPLACE FUNCTION public.sp_save_announcement(p_title character varying, p_content text, p_ann_type character varying, p_status character varying, p_scope character varying, p_creator_id integer, p_creator_role character varying, p_coop_ids integer[], p_officer_ids integer[], p_announcement_id integer DEFAULT NULL::integer, p_scheduled_time timestamp with time zone DEFAULT NULL::timestamp with time zone)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_admin_id INT := NULL;
    v_staff_id INT := NULL;
    v_new_id INT;
    v_rec_id INT;
    v_final_sent_at timestamp with time zone;
BEGIN
    -- 1. ROLE LOGIC (Keep existing logic)
    IF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id FROM admin WHERE user_id = p_creator_id;
        IF v_admin_id IS NULL THEN RAISE EXCEPTION 'User ID % has no admin profile.', p_creator_id; END IF;
    ELSIF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id FROM staff WHERE user_id = p_creator_id;
        IF v_staff_id IS NULL THEN RAISE EXCEPTION 'User ID % has no staff profile.', p_creator_id; END IF;
    ELSE
        RAISE EXCEPTION 'Invalid role';
    END IF;

    -- 2. DATE LOGIC
    -- If explicitly scheduled, use that time. 
    -- If sending NOW ('sent'), use NOW(). 
    -- If draft, use NULL.
    IF p_scheduled_time IS NOT NULL THEN
        v_final_sent_at := p_scheduled_time;
    ELSIF p_status = 'sent' THEN
        v_final_sent_at := NOW();
    ELSE
        v_final_sent_at := NULL;
    END IF;

    -- 3. INSERT OR UPDATE
    IF p_announcement_id IS NULL THEN
        INSERT INTO announcements (
            title, description, "type", status_classification, scope, 
            admin_id, staff_id, sent_at
        )
        VALUES (
            p_title, p_content, p_ann_type::announcement_type_enum, 
            p_status::announcement_status_enum, p_scope, 
            v_admin_id, v_staff_id, v_final_sent_at
        )
        RETURNING announcement_id INTO v_new_id;
    ELSE
        UPDATE announcements 
        SET 
            title = p_title,
            description = p_content,
            "type" = p_ann_type::announcement_type_enum,
            status_classification = p_status::announcement_status_enum,
            scope = p_scope,
            admin_id = v_admin_id,
            staff_id = v_staff_id,
            updated_at = NOW(),
            sent_at = v_final_sent_at -- Update the time
        WHERE announcement_id = p_announcement_id
        RETURNING announcement_id INTO v_new_id;
    END IF;

    -- 4. RECIPIENTS (Keep existing logic)
    DELETE FROM announcement_recipients WHERE announcement_id = v_new_id;
    IF p_coop_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_coop_ids LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id) VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    DELETE FROM announcement_officer_recipients WHERE announcement_id = v_new_id;
    IF p_officer_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_officer_ids LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id) VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    RETURN v_new_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error: %', SQLERRM;
        RETURN NULL;
END;
$function$

CREATE OR REPLACE FUNCTION public.trg_update_first_login_status()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Check the NEW value of verification_status being saved
    -- This 'NEW' variable is special syntax for triggers
    IF NEW.verification_status = 'verified' THEN
        NEW.is_first_login := false;
    ELSIF NEW.verification_status = 'pending' THEN
        NEW.is_first_login := true;
    END IF;
    
    -- Always return the (possibly modified) NEW row to be saved
    RETURN NEW;
END;
$function$

CREATE OR REPLACE FUNCTION public.verify_pbkdf2_sha256(p_password text, p_django_hash text)
 RETURNS boolean
 LANGUAGE plpython3u
AS $function$
    # We are writing Python code inside PostgreSQL
    import hashlib
    import base64

    try:
        # 1. Parse the Django hash string
        # e.g., 'pbkdf2_sha256$1000000$salt$hash'
        algo, iterations, salt, stored_hash_b64 = p_django_hash.split('$', 3)
        
        if algo != 'pbkdf2_sha256':
            return False
        
        iterations = int(iterations)
        
        # 2. Decode the stored hash from Base64
        stored_hash_bytes = base64.b64decode(stored_hash_b64)
        
        # 3. Calculate the new hash using the same parameters
        new_hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            p_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations,
            dklen=len(stored_hash_bytes) # Get the exact length (e.g., 32 bytes)
        )
        
        # 4. Compare the two byte arrays
        return new_hash_bytes == stored_hash_bytes
        
    except Exception:
        # If splitting fails, hash is invalid, etc.
        return False
$function$
