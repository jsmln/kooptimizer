-- Alter messages table to add attachment columns if they do not exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='messages' AND column_name='attachment'
    ) THEN
        ALTER TABLE messages
        ADD COLUMN attachment bytea,
        ADD COLUMN attachment_filename varchar(255),
        ADD COLUMN attachment_content_type varchar(255),
        ADD COLUMN attachment_size bigint;
    END IF;
END$$;
