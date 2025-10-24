CREATE OR REPLACE FUNCTION public.sp_register_user(p_username character varying, p_password character varying, p_role character varying)
 RETURNS users
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_password_hash VARCHAR(128);
    v_new_user users;
BEGIN
    -- Generate a secure hash for the provided password.
    -- crypt() with 'bf' (bcrypt) and a generated salt is recommended.
    v_password_hash := crypt(p_password, gen_salt('bf'));

    -- Insert the new user with the hashed password.
    -- is_first_login defaults to TRUE per your table definition.
    INSERT INTO users (username, password_hash, role, verification_status)
    VALUES (p_username, v_password_hash, p_role, 'pending')
    RETURNING * INTO v_new_user;

    RETURN v_new_user;

EXCEPTION
    -- Handle potential unique constraint violation (username already exists)
    WHEN unique_violation THEN
        RETURN NULL;
END;
$function$


