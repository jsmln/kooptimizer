-- 1. MESSENGER CONVERSATIONS (The "Room" for 1-on-1)
CREATE TABLE messenger_conversations (
    conversation_id SERIAL PRIMARY KEY,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now() -- For sorting inbox
);
CREATE INDEX idx_messenger_conversations_updated ON messenger_conversations(updated_at DESC);

-- 2. MESSENGER PARTICIPANTS (Who is in the room + Read Status)
CREATE TABLE messenger_participants (
    participant_id SERIAL PRIMARY KEY,
    conversation_id integer NOT NULL,
    user_id integer NOT NULL,
    last_read_at timestamp with time zone DEFAULT now(),
    
    CONSTRAINT fk_messenger_cp_conv FOREIGN KEY (conversation_id) REFERENCES messenger_conversations(conversation_id) ON DELETE CASCADE,
    CONSTRAINT fk_messenger_cp_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    -- Ensure a user is only in a conversation once
    CONSTRAINT uniq_messenger_participant UNIQUE (conversation_id, user_id)
);
CREATE INDEX idx_messenger_cp_user ON messenger_participants(user_id);

-- 3. MESSENGER MESSAGES (The actual content)
CREATE TABLE messenger_messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id integer NOT NULL,
    sender_id integer NOT NULL,
    message_text text,
    attachment bytea,
    attachment_filename varchar(255),
    attachment_content_type varchar(255),
    attachment_size bigint,
    sent_at timestamp with time zone DEFAULT now(),
    
    CONSTRAINT fk_messenger_msg_conv FOREIGN KEY (conversation_id) REFERENCES messenger_conversations(conversation_id) ON DELETE CASCADE,
    CONSTRAINT fk_messenger_msg_sender FOREIGN KEY (sender_id) REFERENCES users(user_id)
);
CREATE INDEX idx_messenger_msg_conv ON messenger_messages(conversation_id);

-- 4. TRIGGER: Auto-update conversation timestamp when a message is sent
CREATE OR REPLACE FUNCTION fn_update_messenger_timestamp()
RETURNS trigger AS $$
BEGIN
    UPDATE messenger_conversations 
    SET updated_at = NEW.sent_at 
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_messenger_ts
AFTER INSERT ON messenger_messages
FOR EACH ROW EXECUTE FUNCTION fn_update_messenger_timestamp();


