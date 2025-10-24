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
        -- User does not exist or password invalid
        v_login_status := ('INVALID_USERNAME_OR_PASSWORD', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
    END IF;

    -- 2. Check if the password matches
    -- We pass the stored hash back to crypt() to be used as the salt.
    IF v_user.password_hash = crypt(p_password, v_user.password_hash) THEN
        -- Password is correct!

        -- 3. Get the original is_first_login status
        v_is_first_login_original := v_user.is_first_login;

        -- 4. If it was their first login, update the flag to false
        IF v_is_first_login_original = TRUE THEN
            UPDATE users
            SET
                is_first_login = FALSE,
                updated_at = now()
            WHERE user_id = v_user.user_id;
        END IF;

        -- 5. Return a success status with all required data
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
        v_login_status := ('ERROR', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
END;
$function$
