CREATE OR REPLACE FUNCTION public.sp_set_first_login()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Only update when the verification status actually changes to 'verified'
    IF NEW.verification_status = 'verified'
       AND (OLD.verification_status IS DISTINCT FROM 'verified') THEN
        NEW.is_first_login := FALSE;
    END IF;

    -- Update timestamp
    NEW.updated_at := now();

    RETURN NEW;
END;
$function$
