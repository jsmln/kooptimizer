-- Stored procedure to save or update announcements
-- When sending a draft created by another user, the sender becomes the current user
CREATE OR REPLACE FUNCTION sp_save_announcement(
    p_title VARCHAR(200),
    p_content TEXT,
    p_type announcement_type_enum,
    p_status announcement_status_enum,
    p_scope VARCHAR(50),
    p_creator_id INTEGER,
    p_creator_role VARCHAR(20),
    p_coop_ids INTEGER[],
    p_officer_ids INTEGER[],
    p_announcement_id INTEGER DEFAULT NULL,
    p_scheduled_time TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_announcement_id INTEGER;
    v_staff_id INTEGER;
    v_admin_id INTEGER;
    v_existing_status announcement_status_enum;
    v_coop_id INTEGER;
    v_officer_id INTEGER;
BEGIN
    -- Get staff_id or admin_id based on creator_role
    IF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id FROM staff WHERE user_id = p_creator_id;
        v_admin_id := NULL;
    ELSIF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id FROM admin WHERE user_id = p_creator_id;
        v_staff_id := NULL;
    ELSE
        RAISE EXCEPTION 'Invalid creator role: %', p_creator_role;
    END IF;

    -- If announcement_id is provided, update existing announcement
    IF p_announcement_id IS NOT NULL THEN
        -- Check if announcement exists
        SELECT status_classification INTO v_existing_status
        FROM announcements
        WHERE announcement_id = p_announcement_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Announcement not found: %', p_announcement_id;
        END IF;

        -- When sending a draft (changing status from draft to sent/scheduled),
        -- update the sender to the current user
        IF v_existing_status = 'draft' AND p_status IN ('sent', 'scheduled') THEN
            UPDATE announcements
            SET title = p_title,
                description = p_content,
                type = p_type,
                status_classification = p_status,
                scope = p_scope,
                staff_id = v_staff_id,
                admin_id = v_admin_id,
                sent_at = CASE WHEN p_status = 'sent' THEN NOW() 
                              WHEN p_status = 'scheduled' THEN p_scheduled_time
                              ELSE sent_at END,
                updated_at = NOW()
            WHERE announcement_id = p_announcement_id;
        ELSE
            -- Regular update (draft to draft, or other changes)
            UPDATE announcements
            SET title = p_title,
                description = p_content,
                type = p_type,
                status_classification = p_status,
                scope = p_scope,
                sent_at = CASE WHEN p_status = 'sent' THEN NOW() 
                              WHEN p_status = 'scheduled' THEN p_scheduled_time
                              ELSE sent_at END,
                updated_at = NOW()
            WHERE announcement_id = p_announcement_id;
        END IF;

        v_announcement_id := p_announcement_id;

        -- Clear existing recipients
        DELETE FROM announcement_recipients WHERE announcement_id = p_announcement_id;
        DELETE FROM announcement_officer_recipients WHERE announcement_id = p_announcement_id;
    ELSE
        -- Insert new announcement
        INSERT INTO announcements (
            staff_id, admin_id, title, description, type, 
            status_classification, scope, sent_at
        ) VALUES (
            v_staff_id, v_admin_id, p_title, p_content, p_type,
            p_status, p_scope,
            CASE WHEN p_status = 'sent' THEN NOW() 
                 WHEN p_status = 'scheduled' THEN p_scheduled_time 
                 ELSE NULL END
        )
        RETURNING announcement_id INTO v_announcement_id;
    END IF;

    -- Insert cooperative recipients
    IF p_coop_ids IS NOT NULL AND array_length(p_coop_ids, 1) > 0 THEN
        FOREACH v_coop_id IN ARRAY p_coop_ids
        LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id)
            VALUES (v_announcement_id, v_coop_id)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;

    -- Insert officer recipients
    IF p_officer_ids IS NOT NULL AND array_length(p_officer_ids, 1) > 0 THEN
        FOREACH v_officer_id IN ARRAY p_officer_ids
        LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id)
            VALUES (v_announcement_id, v_officer_id)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;

    RETURN v_announcement_id;
END;
$$;
