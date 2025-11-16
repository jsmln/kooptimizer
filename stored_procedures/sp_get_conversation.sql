-- Stored procedure: sp_get_conversation
-- Returns all messages between two users (sender A and B) where either is sender and the other is recipient
CREATE OR REPLACE FUNCTION sp_get_conversation(
    p_user_a integer,
    p_user_b integer
)
RETURNS TABLE(
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
BEGIN
        RETURN QUERY
        SELECT m.message_id::integer, m.sender_id::integer, mr.receiver_id::integer, m.message::text,
            m.attachment, m.attachment_filename::text, m.attachment_content_type::text, m.attachment_size::bigint, m.sent_at::timestamptz
    FROM messages m
    JOIN message_recipients mr ON mr.message_id = m.message_id
    WHERE (
        (m.sender_id = p_user_a AND mr.receiver_id = p_user_b)
        OR (m.sender_id = p_user_b AND mr.receiver_id = p_user_a)
    )
    ORDER BY m.sent_at;
END;
$$ LANGUAGE plpgsql;
