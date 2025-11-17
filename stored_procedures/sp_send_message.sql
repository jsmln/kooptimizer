-- Stored procedure: sp_send_message
-- Inserts a message and a message_recipient row atomically
-- Returns the inserted message and recipient info so both sender and receiver can see it
CREATE OR REPLACE FUNCTION sp_send_message(
    p_sender_id integer,
    p_receiver_id integer,
    p_message text,
    p_attachment bytea DEFAULT NULL,
    p_attachment_filename text DEFAULT NULL,
    p_attachment_content_type text DEFAULT NULL,
    p_attachment_size bigint DEFAULT NULL
) RETURNS TABLE(
    message_id integer,
    sender_id integer,
    receiver_id integer,
    message text,
    attachment bytea,
    attachment_filename text,
    attachment_content_type text,
    attachment_size bigint,
    sent_at timestamptz
) AS $$
DECLARE
    v_message_id integer;
    v_sent_at timestamptz;
BEGIN
    -- Insert message row
    INSERT INTO messages (sender_id, message, attachment, attachment_filename, attachment_content_type, attachment_size, sent_at)
    VALUES (p_sender_id, p_message, p_attachment, p_attachment_filename, p_attachment_content_type, p_attachment_size, now())
    RETURNING messages.message_id, messages.sent_at INTO v_message_id, v_sent_at;

    -- Insert recipient row
    INSERT INTO message_recipients (message_id, receiver_id, received_at)
    VALUES (v_message_id, p_receiver_id, v_sent_at);

        -- Return the combined result including attachment metadata (cast to expected types)
        RETURN QUERY
        SELECT m.message_id::integer, m.sender_id::integer, mr.receiver_id::integer, m.message::text,
            m.attachment, m.attachment_filename::text, m.attachment_content_type::text, m.attachment_size::bigint, m.sent_at::timestamptz
        FROM messages m
        JOIN message_recipients mr ON mr.message_id = m.message_id
        WHERE m.message_id = v_message_id;
END;
$$ LANGUAGE plpgsql;
