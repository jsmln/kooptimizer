BEGIN;

-- ======================================================
-- A) CLEANUP (for idempotent execution)
-- ======================================================

-- Drop the function first as it depends on types and tables
DROP FUNCTION IF EXISTS public.sp_login_user(character varying, character varying);

-- Drop dependent composite types
DROP TYPE IF EXISTS user_login_status;

-- Drop tables (must be done in dependency order)
DROP TABLE IF EXISTS message_recipients;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS announcement_recipients;
DROP TABLE IF EXISTS announcements;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS financial_data;
DROP TABLE IF EXISTS profile_data;
DROP TABLE IF EXISTS officers;
DROP TABLE IF EXISTS cooperatives;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS users;

-- Drop enums
DROP TYPE IF EXISTS user_role_enum;
DROP TYPE IF EXISTS verification_status_enum;
DROP TYPE IF EXISTS gender_enum;
DROP TYPE IF EXISTS approval_status_enum;
DROP TYPE IF EXISTS announcement_type_enum;


-- ======================================================
-- B) TYPE DEFINITIONS
-- ======================================================

CREATE TYPE user_role_enum AS ENUM ('admin', 'staff', 'officer');
CREATE TYPE verification_status_enum AS ENUM ('pending', 'verified');
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');
CREATE TYPE approval_status_enum AS ENUM ('pending', 'approved');
CREATE TYPE announcement_type_enum AS ENUM ('sms', 'e-mail');

-- Composite type for the stored procedure return value
CREATE TYPE user_login_status AS (
    status VARCHAR(50),
    user_id INTEGER,
    role user_role_enum,
    verification_status verification_status_enum,
    is_first_login_original BOOLEAN
);


-- ======================================================
-- 1) USERS
-- ======================================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role user_role_enum NOT NULL,
    verification_status verification_status_enum DEFAULT 'pending',
    is_first_login BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ======================================================
-- 2) ADMIN (one-to-one with users)
-- ======================================================
CREATE TABLE admin (
    admin_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE
        REFERENCES users(user_id) ON DELETE CASCADE,
    fullname VARCHAR(100),
    position VARCHAR(50),
    gender gender_enum,
    mobile_number VARCHAR(20)
);

-- ======================================================
-- 3) STAFF (one-to-one with users)
-- ======================================================
CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE
        REFERENCES users(user_id) ON DELETE CASCADE,
    fullname VARCHAR(100),
    position VARCHAR(50),
    gender gender_enum,
    mobile_number VARCHAR(20)
);

-- ======================================================
-- 4) COOPERATIVES
-- ======================================================
CREATE TABLE cooperatives (
    coop_id SERIAL PRIMARY KEY,
    staff_id INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL,
    admin_id INTEGER REFERENCES admin(admin_id) ON DELETE SET NULL,
    cooperative_name VARCHAR(200) NOT NULL UNIQUE, -- Added UNIQUE constraint
    mobile_number VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT coop_exactly_one_owner CHECK (
        (staff_id IS NOT NULL AND admin_id IS NULL)
        OR
        (staff_id IS NULL AND admin_id IS NOT NULL)
    )
);

-- ======================================================
-- 5) OFFICERS
-- ======================================================
CREATE TABLE officers (
    officer_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    coop_id INTEGER NOT NULL
        REFERENCES cooperatives(coop_id) ON DELETE CASCADE,
    fullname VARCHAR(100),
    position VARCHAR(50),
    gender gender_enum,
    mobile_number VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ======================================================
-- 6) PROFILE DATA (one-to-one with coop)
-- ======================================================
CREATE TABLE profile_data (
    profile_id SERIAL PRIMARY KEY,
    coop_id INTEGER NOT NULL UNIQUE
        REFERENCES cooperatives(coop_id) ON DELETE CASCADE,
    address VARCHAR(255),
    mobile_number VARCHAR(20),
    email_address VARCHAR(100),
    cda_registration_number VARCHAR(100),
    cda_registration_date DATE,
    lccdc_membership BOOLEAN,
    lccdc_membership_date DATE,
    operation_area VARCHAR(100),
    business_activity VARCHAR(100),
    board_of_directors_count INTEGER,
    salaried_employees_count INTEGER,
    coc_renewal BOOLEAN,
    cote_renewal BOOLEAN,
    coc_attachment BYTEA,
    cote_attachment BYTEA,
    approval_status approval_status_enum,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ======================================================
-- 7) FINANCIAL DATA (one-to-many per coop)
-- ======================================================
CREATE TABLE financial_data (
    financial_id SERIAL PRIMARY KEY,
    coop_id INTEGER NOT NULL
        REFERENCES cooperatives(coop_id) ON DELETE CASCADE,
    assets DECIMAL(20,2) DEFAULT 0,
    paid_up_capital DECIMAL(20,2) DEFAULT 0,
    net_surplus DECIMAL(20,2) DEFAULT 0,
    attachments BYTEA,
    approval_status approval_status_enum,
    report_year INTEGER CHECK (
        report_year >= 1900 AND
        report_year <= EXTRACT(YEAR FROM now()) + 1
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ======================================================
-- 8) MEMBERS
-- ======================================================
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    coop_id INTEGER NOT NULL
        REFERENCES cooperatives(coop_id) ON DELETE CASCADE,
    fullname VARCHAR(100) NOT NULL,
    gender gender_enum,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ======================================================
-- 9) ANNOUNCEMENTS
-- ======================================================
CREATE TABLE announcements (
    announcement_id SERIAL PRIMARY KEY,
    staff_id INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL,
    admin_id INTEGER REFERENCES admin(admin_id) ON DELETE SET NULL,
    description TEXT,
    type announcement_type_enum,
    attachment BYTEA,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    scope VARCHAR(50),
    CONSTRAINT announcement_sender_check CHECK (
        (staff_id IS NOT NULL AND admin_id IS NULL)
        OR
        (staff_id IS NULL AND admin_id IS NOT NULL)
    )
);

-- ======================================================
-- 10) ANNOUNCEMENT RECIPIENTS
-- ======================================================
CREATE TABLE announcement_recipients (
    announcement_id INTEGER NOT NULL
        REFERENCES announcements(announcement_id) ON DELETE CASCADE,
    coop_id INTEGER NOT NULL
        REFERENCES cooperatives(coop_id) ON DELETE CASCADE,
    PRIMARY KEY (announcement_id, coop_id)
);

-- ======================================================
-- 11) MESSAGES
-- ======================================================
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ======================================================
-- 12) MESSAGE RECIPIENTS
-- ======================================================
CREATE TABLE message_recipients (
    message_id INTEGER NOT NULL
        REFERENCES messages(message_id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    received_at TIMESTAMPTZ,
    PRIMARY KEY (message_id, receiver_id)
);


-- ======================================================
-- C) EXTENSIONS & DATA SEEDING
-- ======================================================

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------
-- USERS (3 pending + 3 verified)
-- ------------------------------------------------------


-- ======================================================
-- D) INDEXES (for performance on JOIN and WHERE clauses)
-- ======================================================
CREATE INDEX idx_officers_coop_id ON officers(coop_id);
CREATE INDEX idx_members_coop_id ON members(coop_id);
CREATE INDEX idx_financial_coop_id ON financial_data(coop_id);
CREATE INDEX idx_profile_coop_id ON profile_data(coop_id);


-- ======================================================
-- E) STORED PROCEDURES / FUNCTIONS
-- ======================================================
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
        -- User does not exist or password invalid (return the same error message for security)
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
        RAISE NOTICE 'An error occurred: %', SQLERRM;
        v_login_status := ('ERROR', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
END;
$function$;

COMMIT;



-- Add 'email' to the admin table (making it unique)
ALTER TABLE admin
ADD COLUMN email VARCHAR(100) UNIQUE;

-- Add 'email' to the staff table (making it unique)
ALTER TABLE staff
ADD COLUMN email VARCHAR(100) UNIQUE;

-- Add 'email' to the officers table
ALTER TABLE officers
ADD COLUMN email VARCHAR(100);

-- Add 'title' to the announcements table
ALTER TABLE announcements
ADD COLUMN title VARCHAR(200);


-- ======================================================
-- 10.5) ANNOUNCEMENT OFFICER RECIPIENTS (NEW TABLE)
-- ======================================================
CREATE TABLE announcement_officer_recipients (
    announcement_id INTEGER NOT NULL
        REFERENCES announcements(announcement_id) ON DELETE CASCADE,
    officer_id INTEGER NOT NULL
        REFERENCES officers(officer_id) ON DELETE CASCADE,
    PRIMARY KEY (announcement_id, officer_id)
);

-- Add an index for good performance
CREATE INDEX idx_announcement_officer_recipients_officer_id 
ON announcement_officer_recipients(officer_id);

-- First, create the new ENUM type for the status
CREATE TYPE announcement_status_enum AS ENUM (
    'sent',
    'draft',
    'scheduled'
);

-- Next, add the new column to your announcements table
ALTER TABLE announcements
ADD COLUMN status_classification announcement_status_enum 





CREATE OR REPLACE FUNCTION sp_save_announcement(
    p_title VARCHAR,
    p_content TEXT,
    p_ann_type VARCHAR,       -- Passed as string, e.g., 'sms'
    p_status VARCHAR,         -- Passed as string, e.g., 'draft'
    p_scope VARCHAR,
    p_creator_id INT,         -- This is the USER_ID
    p_creator_role VARCHAR,   -- This is 'admin' or 'staff'
    p_coop_ids INT[],         -- Array of Cooperative IDs
    p_officer_ids INT[],      -- Array of Officer IDs
    p_announcement_id INT DEFAULT NULL
)
RETURNS INT AS $$
DECLARE
    v_admin_id INT := NULL;
    v_staff_id INT := NULL;
    v_new_id INT;
    v_rec_id INT;
BEGIN
    -- ====================================================
    -- 1. TRANSLATE USER_ID TO ADMIN_ID OR STAFF_ID
    -- ====================================================
    
    -- If the creator is an Admin, find their admin_id
    IF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id 
        FROM admin 
        WHERE user_id = p_creator_id;
        
        -- Safety check: if not found, raise error
        IF v_admin_id IS NULL THEN
            RAISE EXCEPTION 'User ID % has role admin but no record found in admin table.', p_creator_id;
        END IF;

    -- If the creator is Staff, find their staff_id
    ELSIF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id 
        FROM staff 
        WHERE user_id = p_creator_id;
        
        IF v_staff_id IS NULL THEN
            RAISE EXCEPTION 'User ID % has role staff but no record found in staff table.', p_creator_id;
        END IF;
    END IF;

    -- ====================================================
    -- 2. INSERT OR UPDATE THE ANNOUNCEMENT
    -- ====================================================
    IF p_announcement_id IS NULL THEN
        -- INSERT NEW
        INSERT INTO announcements (
            title, 
            description, 
            type, 
            status_classification, 
            scope, 
            admin_id,   -- We insert the specific ID here
            staff_id,   -- We insert the specific ID here
            sent_at
        )
        VALUES (
            p_title, 
            p_content, 
            p_ann_type::announcement_type_enum, -- Cast string to ENUM
            p_status, 
            p_scope, 
            v_admin_id, -- Use the translated variable
            v_staff_id, -- Use the translated variable
            NOW()
        )
        RETURNING announcement_id INTO v_new_id;
    ELSE
        -- UPDATE EXISTING
        UPDATE announcements 
        SET 
            title = p_title,
            description = p_content,
            type = p_ann_type::announcement_type_enum,
            status_classification = p_status,
            scope = p_scope,
            updated_at = NOW()
        WHERE announcement_id = p_announcement_id
        RETURNING announcement_id INTO v_new_id;
    END IF;

    -- ====================================================
    -- 3. HANDLE RECIPIENTS (Clear old, Insert new)
    -- ====================================================
    
    -- A. Handle Cooperatives (M2M)
    DELETE FROM announcement_recipients WHERE announcement_id = v_new_id;
    
    IF p_coop_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_coop_ids
        LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id)
            VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    -- B. Handle Officers (M2M)
    DELETE FROM announcement_officer_recipients WHERE announcement_id = v_new_id;
    
    IF p_officer_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_officer_ids
        LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id)
            VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    -- Return the ID to Django
    RETURN v_new_id;

EXCEPTION
    WHEN OTHERS THEN
        -- Log the error message to Postgres logs for debugging
        RAISE NOTICE 'Error saving announcement: %', SQLERRM;
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- 1. First, clean up any old versions
DROP FUNCTION IF EXISTS public.sp_save_announcement(
    character varying, text, character varying, character varying, 
    character varying, integer, character varying, integer[], integer[], integer
);

-- 2. Create the robust version
CREATE OR REPLACE FUNCTION public.sp_save_announcement(
    p_title character varying, 
    p_content text, 
    p_ann_type character varying, -- Input as String ('sms')
    p_status character varying,   -- Input as String ('draft')
    p_scope character varying, 
    p_creator_id integer,         -- The User ID from Django session
    p_creator_role character varying, -- 'admin' or 'staff'
    p_coop_ids integer[], 
    p_officer_ids integer[], 
    p_announcement_id integer DEFAULT NULL::integer
)
RETURNS integer
LANGUAGE plpgsql
AS $function$
DECLARE
    v_admin_id INT := NULL;
    v_staff_id INT := NULL;
    v_new_id INT;
    v_rec_id INT;
BEGIN
    -- ====================================================
    -- 1. LOGIC TO SATISFY "announcement_sender_check"
    -- ====================================================
    -- We translate the User ID into EITHER an Admin ID OR a Staff ID.
    -- The other one stays NULL. This satisfies your table constraint.
    
    IF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id 
        FROM admin WHERE user_id = p_creator_id;
        
        IF v_admin_id IS NULL THEN
            RAISE EXCEPTION 'User ID % is logged in as admin, but has no profile in the admin table.', p_creator_id;
        END IF;
        -- v_staff_id remains NULL

    ELSIF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id 
        FROM staff WHERE user_id = p_creator_id;
        
        IF v_staff_id IS NULL THEN
            RAISE EXCEPTION 'User ID % is logged in as staff, but has no profile in the staff table.', p_creator_id;
        END IF;
        -- v_admin_id remains NULL
    ELSE
        RAISE EXCEPTION 'Invalid role: %. Must be admin or staff.', p_creator_role;
    END IF;

    -- ====================================================
    -- 2. INSERT OR UPDATE
    -- ====================================================
    IF p_announcement_id IS NULL THEN
        INSERT INTO announcements (
            title, 
            description, 
            "type",                 -- Note the quotes, "type" is a reserved word in some SQL
            status_classification, 
            scope, 
            admin_id, 
            staff_id, 
            sent_at
        )
        VALUES (
            p_title, 
            p_content, 
            p_ann_type::announcement_type_enum,      -- CAST string to Enum
            p_status::announcement_status_enum,      -- CAST string to Enum
            p_scope, 
            v_admin_id, 
            v_staff_id, 
            (CASE WHEN p_status = 'sent' THEN NOW() ELSE NULL END)
        )
        RETURNING announcement_id INTO v_new_id;
    ELSE
        UPDATE announcements 
        SET 
            title = p_title,
            description = p_content,
            "type" = p_ann_type::announcement_type_enum,         -- CAST string to Enum
            status_classification = p_status::announcement_status_enum, -- CAST string to Enum
            scope = p_scope,
            admin_id = v_admin_id, -- Updates sender if edited
            staff_id = v_staff_id, -- Updates sender if edited
            updated_at = NOW(),
            sent_at = (CASE WHEN p_status = 'sent' AND sent_at IS NULL THEN NOW() ELSE sent_at END)
        WHERE announcement_id = p_announcement_id
        RETURNING announcement_id INTO v_new_id;
    END IF;

    -- ====================================================
    -- 3. RECIPIENTS
    -- ====================================================
    -- Handle Cooperatives
    DELETE FROM announcement_recipients WHERE announcement_id = v_new_id;
    IF p_coop_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_coop_ids
        LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id)
            VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    -- Handle Officers
    DELETE FROM announcement_officer_recipients WHERE announcement_id = v_new_id;
    IF p_officer_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_officer_ids
        LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id)
            VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    RETURN v_new_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error saving announcement: %', SQLERRM;
        RETURN NULL;
END;
$function$;

ALTER TABLE announcements ALTER COLUMN sent_at DROP NOT NULL;
ALTER TABLE announcements ALTER COLUMN sent_at DROP DEFAULT;

CREATE OR REPLACE FUNCTION public.sp_save_announcement(p_title character varying, p_content text, p_ann_type character varying, p_status character varying, p_scope character varying, p_creator_id integer, p_creator_role character varying, p_coop_ids integer[], p_officer_ids integer[], p_announcement_id integer DEFAULT NULL::integer)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_admin_id INT := NULL;
    v_staff_id INT := NULL;
    v_new_id INT;
    v_rec_id INT;
BEGIN
    -- ====================================================
    -- 1. LOGIC TO SATISFY "announcement_sender_check"
    -- ====================================================
    -- We translate the User ID into EITHER an Admin ID OR a Staff ID.
    -- The other one stays NULL. This satisfies your table constraint.
    
    IF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id 
        FROM admin WHERE user_id = p_creator_id;
        
        IF v_admin_id IS NULL THEN
            RAISE EXCEPTION 'User ID % is logged in as admin, but has no profile in the admin table.', p_creator_id;
        END IF;
        -- v_staff_id remains NULL

    ELSIF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id 
        FROM staff WHERE user_id = p_creator_id;
        
        IF v_staff_id IS NULL THEN
            RAISE EXCEPTION 'User ID % is logged in as staff, but has no profile in the staff table.', p_creator_id;
        END IF;
        -- v_admin_id remains NULL
    ELSE
        RAISE EXCEPTION 'Invalid role: %. Must be admin or staff.', p_creator_role;
    END IF;

    -- ====================================================
    -- 2. INSERT OR UPDATE
    -- ====================================================
    IF p_announcement_id IS NULL THEN
        INSERT INTO announcements (
            title, 
            description, 
            "type",                 -- Note the quotes, "type" is a reserved word in some SQL
            status_classification, 
            scope, 
            admin_id, 
            staff_id, 
            sent_at
        )
        VALUES (
            p_title, 
            p_content, 
            p_ann_type::announcement_type_enum,      -- CAST string to Enum
            p_status::announcement_status_enum,      -- CAST string to Enum
            p_scope, 
            v_admin_id, 
            v_staff_id, 
            (CASE WHEN p_status = 'sent' THEN NOW() ELSE NULL END)
        )
        RETURNING announcement_id INTO v_new_id;
    ELSE
        UPDATE announcements 
        SET 
            title = p_title,
            description = p_content,
            "type" = p_ann_type::announcement_type_enum,         -- CAST string to Enum
            status_classification = p_status::announcement_status_enum, -- CAST string to Enum
            scope = p_scope,
            admin_id = v_admin_id, -- Updates sender if edited
            staff_id = v_staff_id, -- Updates sender if edited
            updated_at = NOW(),
            sent_at = (CASE WHEN p_status = 'sent' AND sent_at IS NULL THEN NOW() ELSE sent_at END)
        WHERE announcement_id = p_announcement_id
        RETURNING announcement_id INTO v_new_id;
    END IF;

    -- ====================================================
    -- 3. RECIPIENTS
    -- ====================================================
    -- Handle Cooperatives
    DELETE FROM announcement_recipients WHERE announcement_id = v_new_id;
    IF p_coop_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_coop_ids
        LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id)
            VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    -- Handle Officers
    DELETE FROM announcement_officer_recipients WHERE announcement_id = v_new_id;
    IF p_officer_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_officer_ids
        LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id)
            VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    RETURN v_new_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error saving announcement: %', SQLERRM;
        RETURN NULL;
END;
$function$


DROP FUNCTION IF EXISTS public.sp_save_announcement(
    character varying, text, character varying, character varying, 
    character varying, integer, character varying, integer[], integer[], integer
);

CREATE OR REPLACE FUNCTION public.sp_save_announcement(
    p_title character varying, 
    p_content text, 
    p_ann_type character varying, 
    p_status character varying, 
    p_scope character varying, 
    p_creator_id integer, 
    p_creator_role character varying, 
    p_coop_ids integer[], 
    p_officer_ids integer[], 
    p_announcement_id integer DEFAULT NULL::integer,
    p_scheduled_time timestamp with time zone DEFAULT NULL -- NEW PARAMETER
)
RETURNS integer
LANGUAGE plpgsql
AS $function$
DECLARE
    v_admin_id INT := NULL;
    v_staff_id INT := NULL;
    v_new_id INT;
    v_rec_id INT;
    v_final_sent_at timestamp with time zone;
BEGIN
    -- 1. ROLE LOGIC (Keep existing logic)
    IF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id FROM admin WHERE user_id = p_creator_id;
        IF v_admin_id IS NULL THEN RAISE EXCEPTION 'User ID % has no admin profile.', p_creator_id; END IF;
    ELSIF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id FROM staff WHERE user_id = p_creator_id;
        IF v_staff_id IS NULL THEN RAISE EXCEPTION 'User ID % has no staff profile.', p_creator_id; END IF;
    ELSE
        RAISE EXCEPTION 'Invalid role';
    END IF;

    -- 2. DATE LOGIC
    -- If explicitly scheduled, use that time. 
    -- If sending NOW ('sent'), use NOW(). 
    -- If draft, use NULL.
    IF p_scheduled_time IS NOT NULL THEN
        v_final_sent_at := p_scheduled_time;
    ELSIF p_status = 'sent' THEN
        v_final_sent_at := NOW();
    ELSE
        v_final_sent_at := NULL;
    END IF;

    -- 3. INSERT OR UPDATE
    IF p_announcement_id IS NULL THEN
        INSERT INTO announcements (
            title, description, "type", status_classification, scope, 
            admin_id, staff_id, sent_at
        )
        VALUES (
            p_title, p_content, p_ann_type::announcement_type_enum, 
            p_status::announcement_status_enum, p_scope, 
            v_admin_id, v_staff_id, v_final_sent_at
        )
        RETURNING announcement_id INTO v_new_id;
    ELSE
        UPDATE announcements 
        SET 
            title = p_title,
            description = p_content,
            "type" = p_ann_type::announcement_type_enum,
            status_classification = p_status::announcement_status_enum,
            scope = p_scope,
            admin_id = v_admin_id,
            staff_id = v_staff_id,
            updated_at = NOW(),
            sent_at = v_final_sent_at -- Update the time
        WHERE announcement_id = p_announcement_id
        RETURNING announcement_id INTO v_new_id;
    END IF;

    -- 4. RECIPIENTS (Keep existing logic)
    DELETE FROM announcement_recipients WHERE announcement_id = v_new_id;
    IF p_coop_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_coop_ids LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id) VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    DELETE FROM announcement_officer_recipients WHERE announcement_id = v_new_id;
    IF p_officer_ids IS NOT NULL THEN
        FOREACH v_rec_id IN ARRAY p_officer_ids LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id) VALUES (v_new_id, v_rec_id);
        END LOOP;
    END IF;

    RETURN v_new_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error: %', SQLERRM;
        RETURN NULL;
END;
$function$;