-- Update stored procedure to include attachment information
-- Run this in your PostgreSQL database (kooptimizer)

-- Drop the existing function first (required when changing return type)
DROP FUNCTION IF EXISTS public.sp_get_announcements_by_statuses(announcement_status_enum);

-- Create the function with updated return type
CREATE FUNCTION public.sp_get_announcements_by_statuses(p_status announcement_status_enum)
 RETURNS TABLE(
    announcement_id integer, 
    title character varying, 
    description text, 
    type announcement_type_enum, 
    status_classification announcement_status_enum, 
    scope character varying, 
    sent_at timestamp with time zone, 
    created_at timestamp with time zone, 
    updated_at timestamp with time zone, 
    creator_name character varying, 
    has_attachment boolean, 
    attachment_count integer
)
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
        COALESCE(s.fullname, adm.fullname, 'Unknown') AS creator_name,
        CASE WHEN a.attachment_size IS NOT NULL AND a.attachment_size > 0 THEN TRUE ELSE FALSE END AS has_attachment,
        CASE 
            WHEN a.attachment_filename IS NOT NULL THEN 
                array_length(string_to_array(a.attachment_filename, ';'), 1)
            ELSE 0 
        END AS attachment_count
    FROM
        announcements a
    LEFT JOIN
        staff s ON a.staff_id = s.staff_id
    LEFT JOIN
        admin adm ON a.admin_id = adm.admin_id
    WHERE
        a.status_classification = p_status
    ORDER BY
        a.updated_at DESC;
END;
$function$;

-- Verify the update
SELECT * FROM sp_get_announcements_by_statuses('sent') LIMIT 5;
