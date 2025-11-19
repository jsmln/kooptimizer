-- Get detailed announcement information including recipients
CREATE OR REPLACE FUNCTION sp_get_announcement_details(
    p_announcement_id INTEGER
)
RETURNS TABLE (
    announcement_id INTEGER,
    title VARCHAR(200),
    description TEXT,
    type announcement_type_enum,
    status_classification announcement_status_enum,
    scope VARCHAR(50),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    attachment_size INTEGER,
    attachment_filename VARCHAR(255),
    sender_name VARCHAR(100),
    sender_role VARCHAR(20),
    coop_recipients TEXT,
    officer_recipients TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_sender_name VARCHAR(100);
    v_sender_role VARCHAR(20);
    v_coop_list TEXT;
    v_officer_list TEXT;
    v_attachment_size INTEGER;
BEGIN
    -- Get sender information
    SELECT 
        CASE 
            WHEN a.admin_id IS NOT NULL THEN 
                COALESCE(ad.fullname, u_admin.username)
            WHEN a.staff_id IS NOT NULL THEN 
                COALESCE(s.fullname, u_staff.username)
            ELSE 'Unknown'
        END,
        CASE 
            WHEN a.admin_id IS NOT NULL THEN 'admin'
            WHEN a.staff_id IS NOT NULL THEN 'staff'
            ELSE 'unknown'
        END
    INTO v_sender_name, v_sender_role
    FROM announcements a
    LEFT JOIN admin ad ON a.admin_id = ad.admin_id
    LEFT JOIN users u_admin ON ad.user_id = u_admin.user_id
    LEFT JOIN staff s ON a.staff_id = s.staff_id
    LEFT JOIN users u_staff ON s.user_id = u_staff.user_id
    WHERE a.announcement_id = p_announcement_id;

    -- Get cooperative recipients as JSON array
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'coop_id', c.coop_id,
                'coop_name', c.cooperative_name
            )
            ORDER BY c.cooperative_name
        )::TEXT,
        '[]'
    )
    INTO v_coop_list
    FROM announcement_recipients ar
    JOIN cooperatives c ON ar.coop_id = c.coop_id
    WHERE ar.announcement_id = p_announcement_id;

    -- Get officer recipients as JSON array with their cooperative info
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'officer_id', o.officer_id,
                'officer_name', o.fullname,
                'coop_id', c.coop_id,
                'coop_name', c.cooperative_name
            )
            ORDER BY c.cooperative_name, o.fullname
        )::TEXT,
        '[]'
    )
    INTO v_officer_list
    FROM announcement_officer_recipients aor
    JOIN officers o ON aor.officer_id = o.officer_id
    JOIN cooperatives c ON o.coop_id = c.coop_id
    WHERE aor.announcement_id = p_announcement_id;

    -- Get attachment size
    SELECT 
        CASE 
            WHEN a.attachment IS NOT NULL THEN COALESCE(a.attachment_size, octet_length(a.attachment))
            ELSE NULL
        END
    INTO v_attachment_size
    FROM announcements a
    WHERE a.announcement_id = p_announcement_id;

    -- Return announcement details
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
        COALESCE(a.attachment_size, v_attachment_size) AS attachment_size,
        a.attachment_filename,
        v_sender_name,
        v_sender_role,
        v_coop_list,
        v_officer_list
    FROM announcements a
    WHERE a.announcement_id = p_announcement_id;
END;
$$;
