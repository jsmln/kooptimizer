--
-- PostgreSQL database dump - SCHEMA ONLY (no data)
-- Database: kooptimizer_db2
-- Generated: December 6, 2025
--
-- This file contains the complete database schema including:
--   - 34 Tables (users, cooperatives, profiles, notifications, etc.)
--   - 39 Functions (stored procedures, triggers, utility functions)
--   - 10 Procedures (account creation, updates, deletions)
--   - 7 Custom Types/Enums (user_role_enum, gender_enum, approval_status_enum, etc.)
--   - 37 Indexes (for performance optimization)
--   - Foreign key constraints and relationships
--   - Trigger definitions
--
-- To restore this schema to a new database:
--   psql -U postgres -d <new_database> -f db/schema.sql
--
-- To apply this to an existing database (use with caution):
--   psql -U postgres -d <database> -f db/schema.sql
--
\restrict zNxxTyp9rMInyJr9OKMGOe0LSnYst7xtVAfMx8Zgsm1IrmpXdXGv8aC8gVwUdCa

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpython3u; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpython3u WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpython3u; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpython3u IS 'PL/Python3U untrusted procedural language';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: announcement_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.announcement_status_enum AS ENUM (
    'sent',
    'draft',
    'scheduled'
);


ALTER TYPE public.announcement_status_enum OWNER TO postgres;

--
-- Name: announcement_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.announcement_type_enum AS ENUM (
    'sms',
    'e-mail'
);


ALTER TYPE public.announcement_type_enum OWNER TO postgres;

--
-- Name: approval_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.approval_status_enum AS ENUM (
    'pending',
    'approved'
);


ALTER TYPE public.approval_status_enum OWNER TO postgres;

--
-- Name: gender_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.gender_enum AS ENUM (
    'male',
    'female',
    'other',
    'others'
);


ALTER TYPE public.gender_enum OWNER TO postgres;

--
-- Name: user_role_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_role_enum AS ENUM (
    'admin',
    'staff',
    'officer'
);


ALTER TYPE public.user_role_enum OWNER TO postgres;

--
-- Name: verification_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.verification_status_enum AS ENUM (
    'pending',
    'verified'
);


ALTER TYPE public.verification_status_enum OWNER TO postgres;

--
-- Name: user_login_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_login_status AS (
	status character varying(50),
	user_id integer,
	role public.user_role_enum,
	verification_status public.verification_status_enum,
	is_first_login_original boolean
);


ALTER TYPE public.user_login_status OWNER TO postgres;

--
-- Name: create_cooperative_profile(integer, character varying, character varying, character varying, character varying, date, boolean, date, character varying, character varying, integer, integer, boolean, boolean, bytea, bytea, numeric, numeric, numeric, bytea, integer, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.create_cooperative_profile(p_coop_id integer, p_address character varying, p_mobile_number character varying, p_email_address character varying, p_cda_registration_number character varying, p_cda_registration_date date, p_lccdc_membership boolean, p_lccdc_membership_date date, p_operation_area character varying, p_business_activity character varying, p_board_of_directors_count integer, p_salaried_employees_count integer, p_coc_renewal boolean, p_cote_renewal boolean, p_coc_attachment bytea, p_cote_attachment bytea, p_assets numeric, p_paid_up_capital numeric, p_net_surplus numeric, p_financial_attachments bytea, p_report_year integer, p_members_json text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_profile_id INTEGER;
    v_financial_id INTEGER;
    v_member JSONB;
BEGIN
    -- Insert profile data
    INSERT INTO profile_data (
        coop_id, address, mobile_number, email_address,
        cda_registration_number, cda_registration_date,
        lccdc_membership, lccdc_membership_date,
        operation_area, business_activity,
        board_of_directors_count, salaried_employees_count,
        coc_renewal, cote_renewal,
        coc_attachment, cote_attachment,
        approval_status
    ) VALUES (
        p_coop_id, p_address, p_mobile_number, p_email_address,
        p_cda_registration_number, p_cda_registration_date,
        p_lccdc_membership, p_lccdc_membership_date,
        p_operation_area, p_business_activity,
        p_board_of_directors_count, p_salaried_employees_count,
        p_coc_renewal, p_cote_renewal,
        p_coc_attachment, p_cote_attachment,
        'pending'
    )
    RETURNING profile_id INTO v_profile_id;
    
    -- Insert financial data
    INSERT INTO financial_data (
        coop_id, assets, paid_up_capital, net_surplus,
        attachments, report_year, approval_status
    ) VALUES (
        p_coop_id, p_assets, p_paid_up_capital, p_net_surplus,
        p_financial_attachments, p_report_year, 'pending'
    )
    RETURNING financial_id INTO v_financial_id;
    
    -- Insert members
    IF p_members_json IS NOT NULL AND p_members_json != '' THEN
        FOR v_member IN SELECT * FROM jsonb_array_elements(p_members_json::jsonb)
        LOOP
            INSERT INTO members (
                coop_id, fullname, gender, mobile_number, email
            ) VALUES (
                p_coop_id,
                v_member->>'fullname',
                (v_member->>'gender')::gender_enum,
                v_member->>'mobile_number',
                v_member->>'email'
            );
        END LOOP;
    END IF;
    
    RETURN v_profile_id;
END;
$$;


ALTER FUNCTION public.create_cooperative_profile(p_coop_id integer, p_address character varying, p_mobile_number character varying, p_email_address character varying, p_cda_registration_number character varying, p_cda_registration_date date, p_lccdc_membership boolean, p_lccdc_membership_date date, p_operation_area character varying, p_business_activity character varying, p_board_of_directors_count integer, p_salaried_employees_count integer, p_coc_renewal boolean, p_cote_renewal boolean, p_coc_attachment bytea, p_cote_attachment bytea, p_assets numeric, p_paid_up_capital numeric, p_net_surplus numeric, p_financial_attachments bytea, p_report_year integer, p_members_json text) OWNER TO postgres;

--
-- Name: fn_trigger_set_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_trigger_set_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_trigger_set_timestamp() OWNER TO postgres;

--
-- Name: fn_update_messenger_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_update_messenger_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE messenger_conversations 
    SET updated_at = NEW.sent_at 
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_update_messenger_timestamp() OWNER TO postgres;

--
-- Name: get_all_profiles_admin(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_all_profiles_admin() RETURNS TABLE(profile_id integer, coop_name character varying, coop_address character varying, district character varying, category character varying, contact character varying, email character varying, cda_reg_num character varying, cda_reg_date date, status public.approval_status_enum, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pd.profile_id,
        c.cooperative_name,
        pd.address,
        c.district,
        c.category,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.approval_status,
        pd.created_at
    FROM profile_data pd
    INNER JOIN cooperatives c ON pd.coop_id = c.coop_id
    ORDER BY pd.created_at DESC;
END;
$$;


ALTER FUNCTION public.get_all_profiles_admin() OWNER TO postgres;

--
-- Name: get_all_user_accounts(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_all_user_accounts() RETURNS TABLE(formatted_id character varying, user_id integer, fullname character varying, email character varying, mobile_number character varying, "position" character varying, coop_name character varying, account_type character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    -- 1. Fetch STAFF
    SELECT 
        ('S' || LPAD(s.staff_id::text, 3, '0'))::VARCHAR as formatted_id,
        s.user_id,
        s.fullname,
        s.email,
        s.mobile_number,
        s.position,
        COALESCE(c.cooperative_name, 'N/A') as coop_name,
        -- FIX: Cast 'Staff' to VARCHAR
        'Staff'::VARCHAR as account_type
    FROM staff s
    JOIN users u ON s.user_id = u.user_id
    LEFT JOIN cooperatives c ON s.staff_id = c.staff_id
    WHERE u.is_active = true

    UNION ALL

    -- 2. Fetch OFFICERS
    SELECT 
        ('O' || LPAD(o.officer_id::text, 3, '0'))::VARCHAR as formatted_id,
        o.user_id,
        o.fullname,
        o.email,
        o.mobile_number,
        o.position,
        c.cooperative_name as coop_name,
        -- FIX: Cast 'Officer' to VARCHAR
        'Officer'::VARCHAR as account_type
    FROM officers o
    JOIN users u ON o.user_id = u.user_id
    LEFT JOIN cooperatives c ON o.coop_id = c.coop_id
    WHERE u.is_active = true

    UNION ALL

    -- 3. Fetch ADMINS
    SELECT 
        ('A' || LPAD(a.admin_id::text, 3, '0'))::VARCHAR as formatted_id,
        a.user_id,
        a.fullname,
        a.email,
        a.mobile_number,
        a.position,
        'N/A' as coop_name,
        -- FIX: Cast 'Admin' to VARCHAR
        'Admin'::VARCHAR as account_type
    FROM admin a
    JOIN users u ON a.user_id = u.user_id
    WHERE u.is_active = true;

END;
$$;


ALTER FUNCTION public.get_all_user_accounts() OWNER TO postgres;

--
-- Name: get_coop_profile_details(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_coop_profile_details(p_coop_id integer) RETURNS TABLE(profile_id integer, coop_name character varying, coop_address character varying, district character varying, category character varying, contact character varying, email character varying, cda_reg_num character varying, cda_reg_date date, lccdc_member boolean, lccdc_date date, operation_area character varying, business_activity character varying, num_bod integer, num_employees integer, has_coc boolean, has_cte boolean, assets numeric, paid_up_capital numeric, net_surplus numeric, report_year integer, status public.approval_status_enum, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pd.profile_id,
        c.cooperative_name,
        pd.address,
        c.district,
        c.category,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.lccdc_membership,
        pd.lccdc_membership_date,
        pd.operation_area,
        pd.business_activity,
        pd.board_of_directors_count,
        pd.salaried_employees_count,
        pd.coc_renewal,
        pd.cote_renewal,
        fd.assets,
        fd.paid_up_capital,
        fd.net_surplus,
        fd.report_year,
        pd.approval_status,
        pd.created_at
    FROM profile_data pd
    INNER JOIN cooperatives c ON pd.coop_id = c.coop_id
    LEFT JOIN financial_data fd ON fd.coop_id = c.coop_id
    WHERE c.coop_id = p_coop_id;
END;
$$;


ALTER FUNCTION public.get_coop_profile_details(p_coop_id integer) OWNER TO postgres;

--
-- Name: get_profile_by_coop(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_profile_by_coop(p_coop_id integer) RETURNS TABLE(profile_id integer, coop_name character varying, coop_address character varying, district character varying, category character varying, contact character varying, email character varying, cda_reg_num character varying, cda_reg_date date, status public.approval_status_enum, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pd.profile_id,
        c.cooperative_name,
        pd.address,
        c.district,
        c.category,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.approval_status,
        pd.created_at
    FROM profile_data pd
    INNER JOIN cooperatives c ON pd.coop_id = c.coop_id
    WHERE c.coop_id = p_coop_id
    ORDER BY pd.created_at DESC;
END;
$$;


ALTER FUNCTION public.get_profile_by_coop(p_coop_id integer) OWNER TO postgres;

--
-- Name: get_profile_details(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_profile_details(p_profile_id integer) RETURNS TABLE(profile_id integer, coop_name character varying, coop_address character varying, district character varying, category character varying, contact character varying, email character varying, cda_reg_num character varying, cda_reg_date date, lccdc_member boolean, lccdc_date date, operation_area character varying, business_activity character varying, num_bod integer, num_employees integer, has_coc boolean, has_cte boolean, assets numeric, paid_up_capital numeric, net_surplus numeric, report_year integer, status public.approval_status_enum, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pd.profile_id,
        c.cooperative_name,
        pd.address,
        c.district,
        c.category,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.lccdc_membership,
        pd.lccdc_membership_date,
        pd.operation_area,
        pd.business_activity,
        pd.board_of_directors_count,
        pd.salaried_employees_count,
        pd.coc_renewal,
        pd.cote_renewal,
        fd.assets,
        fd.paid_up_capital,
        fd.net_surplus,
        fd.report_year,
        pd.approval_status,
        pd.created_at
    FROM profile_data pd
    INNER JOIN cooperatives c ON pd.coop_id = c.coop_id
    LEFT JOIN financial_data fd ON fd.coop_id = c.coop_id
    WHERE pd.profile_id = p_profile_id;
END;
$$;


ALTER FUNCTION public.get_profile_details(p_profile_id integer) OWNER TO postgres;

--
-- Name: get_profiles_by_staff(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_profiles_by_staff(p_staff_id integer) RETURNS TABLE(profile_id integer, coop_name character varying, coop_address character varying, district character varying, category character varying, contact character varying, email character varying, cda_reg_num character varying, cda_reg_date date, status public.approval_status_enum, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pd.profile_id,
        c.cooperative_name,
        pd.address,
        c.district,
        c.category,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.approval_status,
        pd.created_at
    FROM profile_data pd
    INNER JOIN cooperatives c ON pd.coop_id = c.coop_id
    WHERE c.staff_id = p_staff_id
    ORDER BY pd.created_at DESC;
END;
$$;


ALTER FUNCTION public.get_profiles_by_staff(p_staff_id integer) OWNER TO postgres;

--
-- Name: sp_add_coop_profile(integer, character varying, character varying, character varying, character varying, date, boolean, date, character varying, character varying, integer, integer, boolean, boolean, bytea, bytea, numeric, numeric, numeric, bytea, integer, jsonb); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_add_coop_profile(IN p_coop_id integer, IN p_address character varying, IN p_mobile character varying, IN p_email character varying, IN p_cda_reg character varying, IN p_cda_date date, IN p_lccdc_mem boolean, IN p_lccdc_date date, IN p_area character varying, IN p_bus_act character varying, IN p_bod_count integer, IN p_emp_count integer, IN p_coc_renew boolean, IN p_cote_renew boolean, IN p_coc_file bytea, IN p_cote_file bytea, IN p_assets numeric, IN p_paid_up numeric, IN p_net_surplus numeric, IN p_fin_file bytea, IN p_report_year integer, IN p_members_json jsonb)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_profile_id INT;
    rec JSONB;
BEGIN
    -- 1. Insert Profile Data
    INSERT INTO profile_data (
        coop_id, address, mobile_number, email_address, cda_registration_number, 
        cda_registration_date, lccdc_membership, lccdc_membership_date, 
        operation_area, business_activity, board_of_directors_count, 
        salaried_employees_count, coc_renewal, cote_renewal, 
        coc_attachment, cote_attachment, approval_status
    ) VALUES (
        p_coop_id, p_address, p_mobile, p_email, p_cda_reg, 
        p_cda_date, p_lccdc_mem, p_lccdc_date, 
        p_area, p_bus_act, p_bod_count, 
        p_emp_count, p_coc_renew, p_cote_renew, 
        p_coc_file, p_cote_file, 'pending'
    ) RETURNING profile_id INTO v_profile_id;

    -- 2. Insert Financial Data
    INSERT INTO financial_data (
        coop_id, assets, paid_up_capital, net_surplus, 
        attachments, report_year, approval_status
    ) VALUES (
        p_coop_id, p_assets, p_paid_up, p_net_surplus, 
        p_fin_file, p_report_year, 'pending'
    );

    -- 3. Insert Members (Iterate through JSON input)
    -- JSON structure expected: [{"name": "...", "gender": "...", "mobile": "...", "email": "..."}]
    FOR rec IN SELECT * FROM jsonb_array_elements(p_members_json)
    LOOP
        INSERT INTO members (coop_id, fullname, gender, mobile, email)
        VALUES (
            p_coop_id, 
            rec->>'name', 
            (rec->>'gender')::gender_enum, 
            rec->>'mobile',
            rec->>'email'
        );
    END LOOP;

    COMMIT;
END;
$$;


ALTER PROCEDURE public.sp_add_coop_profile(IN p_coop_id integer, IN p_address character varying, IN p_mobile character varying, IN p_email character varying, IN p_cda_reg character varying, IN p_cda_date date, IN p_lccdc_mem boolean, IN p_lccdc_date date, IN p_area character varying, IN p_bus_act character varying, IN p_bod_count integer, IN p_emp_count integer, IN p_coc_renew boolean, IN p_cote_renew boolean, IN p_coc_file bytea, IN p_cote_file bytea, IN p_assets numeric, IN p_paid_up numeric, IN p_net_surplus numeric, IN p_fin_file bytea, IN p_report_year integer, IN p_members_json jsonb) OWNER TO postgres;

--
-- Name: sp_complete_first_login(integer, character varying, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_verification_status_text character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE users
    SET
        password_hash = p_new_password_hash,
        
        -- THIS IS THE FIX for your error:
        -- We explicitly CAST the text from Python to the enum type
        verification_status = p_verification_status_text::verification_status_enum,
        
        updated_at = NOW()
        
        -- We NO LONGER need to set is_first_login here!
        -- The trigger will handle it automatically.
    WHERE
        user_id = p_user_id;
END;
$$;


ALTER FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_verification_status_text character varying) OWNER TO postgres;

--
-- Name: sp_complete_first_login(integer, character varying, boolean, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_is_first_login boolean, p_verification_status character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE users
    SET
        password_hash = p_new_password_hash,
        is_first_login = p_is_first_login,
        verification_status = p_verification_status,
        updated_at = NOW()
    WHERE
        user_id = p_user_id;
END;
$$;


ALTER FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_is_first_login boolean, p_verification_status character varying) OWNER TO postgres;

--
-- Name: sp_complete_first_login(integer, character varying, boolean, public.verification_status_enum); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_is_first_login boolean, p_verification_status public.verification_status_enum) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE users
    SET
        password_hash = p_new_password_hash,
        is_first_login = p_is_first_login,
        verification_status = p_verification_status,
        updated_at = NOW()
    WHERE
        user_id = p_user_id;
END;
$$;


ALTER FUNCTION public.sp_complete_first_login(p_user_id integer, p_new_password_hash character varying, p_is_first_login boolean, p_verification_status public.verification_status_enum) OWNER TO postgres;

--
-- Name: sp_create_admin_account(character varying, character varying, character varying, character varying, character varying, character varying); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_create_admin_account(IN p_hash character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying)
    LANGUAGE plpgsql
    AS $$
DECLARE v_uid INT;
BEGIN
    INSERT INTO users (username, password_hash, role, verification_status) 
    VALUES (p_email, p_hash, 'admin', 'pending') RETURNING user_id INTO v_uid;
    
    INSERT INTO admin (user_id, fullname, position, gender, mobile_number, email)
    VALUES (v_uid, p_name, p_pos, p_gender::gender_enum, p_mobile, p_email);
END; $$;


ALTER PROCEDURE public.sp_create_admin_account(IN p_hash character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying) OWNER TO postgres;

--
-- Name: sp_create_cooperative(integer, character varying, character varying, character varying, character varying, character varying, character varying, character varying, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_create_cooperative(_staff_id integer, _coop_name character varying, _category character varying, _district character varying, _address character varying, _mobile character varying, _email character varying, _cda_no character varying, _cda_date date) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    new_coop_id INT;
BEGIN
    -- 1. Insert into base table
    INSERT INTO cooperatives (staff_id, cooperative_name, category, district)
    VALUES (_staff_id, _coop_name, _category, _district)
    RETURNING coop_id INTO new_coop_id;

    -- 2. Insert into profile_data (initialize)
    INSERT INTO profile_data (coop_id, address, mobile_number, email_address, cda_registration_number, cda_registration_date, approval_status)
    VALUES (new_coop_id, _address, _mobile, _email, _cda_no, _cda_date, 'Pending');

    -- 3. Insert into financial_data (initialize)
    INSERT INTO financial_data (coop_id, approval_status)
    VALUES (new_coop_id, 'Pending');

    RETURN new_coop_id;
END;
$$;


ALTER FUNCTION public.sp_create_cooperative(_staff_id integer, _coop_name character varying, _category character varying, _district character varying, _address character varying, _mobile character varying, _email character varying, _cda_no character varying, _cda_date date) OWNER TO postgres;

--
-- Name: sp_create_officer_account(character varying, character varying, character varying, character varying, character varying, character varying, integer); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_create_officer_account(IN p_hash character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying, IN p_coop_id integer)
    LANGUAGE plpgsql
    AS $$
DECLARE v_uid INT;
BEGIN
    INSERT INTO users (username, password_hash, role, verification_status) 
    VALUES (p_email, p_hash, 'officer', 'pending') RETURNING user_id INTO v_uid;

    INSERT INTO officers (user_id, coop_id, fullname, position, gender, mobile_number, email)
    VALUES (v_uid, p_coop_id, p_name, p_pos, p_gender::gender_enum, p_mobile, p_email);
END; $$;


ALTER PROCEDURE public.sp_create_officer_account(IN p_hash character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying, IN p_coop_id integer) OWNER TO postgres;

--
-- Name: sp_create_profile(integer, character varying, character varying, character varying, character varying, date, boolean, date, character varying, character varying, integer, integer, boolean, bytea, boolean, bytea, numeric, numeric, numeric, bytea, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_create_profile(p_coop_id integer, p_address character varying, p_mobile character varying, p_email character varying, p_cda_registration_number character varying, p_cda_registration_date date, p_lccdc_membership boolean, p_lccdc_membership_date date, p_operation_area character varying, p_business_activity character varying, p_board_of_directors_count integer, p_salaried_employees_count integer, p_coc_renewal boolean, p_coc_attachment bytea, p_cote_renewal boolean, p_cote_attachment bytea, p_assets numeric, p_paid_up_capital numeric, p_net_surplus numeric, p_financial_attachments bytea, p_report_year integer) RETURNS TABLE(profile_id integer, financial_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Insert or update profile_data (depending on whether a profile exists for the coop_id)
    IF EXISTS (SELECT 1 FROM profile_data WHERE coop_id = p_coop_id) THEN
        UPDATE profile_data
        SET address = p_address,
            mobile_number = p_mobile,
            email_address = p_email,
            cda_registration_number = p_cda_registration_number,
            cda_registration_date = p_cda_registration_date,
            lccdc_membership = p_lccdc_membership,
            lccdc_membership_date = p_lccdc_membership_date,
            operation_area = p_operation_area,
            business_activity = p_business_activity,
            board_of_directors_count = p_board_of_directors_count,
            salaried_employees_count = p_salaried_employees_count,
            coc_renewal = p_coc_renewal,
            cote_renewal = p_cote_renewal,
            coc_attachment = p_coc_attachment,
            cote_attachment = p_cote_attachment,
            updated_at = now()
        WHERE coop_id = p_coop_id
        RETURNING profile_id INTO profile_id;
    ELSE
        INSERT INTO profile_data(
            coop_id, address, mobile_number, email_address,
            cda_registration_number, cda_registration_date,
            lccdc_membership, lccdc_membership_date,
            operation_area, business_activity,
            board_of_directors_count, salaried_employees_count,
            coc_renewal, cote_renewal, coc_attachment, cote_attachment,
            created_at, updated_at
        ) VALUES (
            p_coop_id, p_address, p_mobile, p_email,
            p_cda_registration_number, p_cda_registration_date,
            p_lccdc_membership, p_lccdc_membership_date,
            p_operation_area, p_business_activity,
            p_board_of_directors_count, p_salaried_employees_count,
            p_coc_renewal, p_cote_renewal, p_coc_attachment, p_cote_attachment,
            now(), now()
        )
        RETURNING profile_id INTO profile_id;
    END IF;

    -- Insert a new financial_data row (we don't update existing financial_data here to preserve history; adjust if you want to upsert)
    INSERT INTO financial_data(
        coop_id, assets, paid_up_capital, net_surplus,
        attachments, report_year, created_at, updated_at
    ) VALUES (
        p_coop_id, COALESCE(p_assets, 0), COALESCE(p_paid_up_capital, 0), COALESCE(p_net_surplus, 0),
        p_financial_attachments, p_report_year, now(), now()
    )
    RETURNING financial_id INTO financial_id;

    RETURN NEXT;
END;
$$;


ALTER FUNCTION public.sp_create_profile(p_coop_id integer, p_address character varying, p_mobile character varying, p_email character varying, p_cda_registration_number character varying, p_cda_registration_date date, p_lccdc_membership boolean, p_lccdc_membership_date date, p_operation_area character varying, p_business_activity character varying, p_board_of_directors_count integer, p_salaried_employees_count integer, p_coc_renewal boolean, p_coc_attachment bytea, p_cote_renewal boolean, p_cote_attachment bytea, p_assets numeric, p_paid_up_capital numeric, p_net_surplus numeric, p_financial_attachments bytea, p_report_year integer) OWNER TO postgres;

--
-- Name: sp_create_staff_account(character varying, character varying, character varying, character varying, character varying, character varying, integer[]); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_create_staff_account(IN p_hash character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying, IN p_coop_ids integer[])
    LANGUAGE plpgsql
    AS $$
DECLARE v_uid INT; v_sid INT; v_cid INT;
BEGIN
    INSERT INTO users (username, password_hash, role, verification_status) 
    VALUES (p_email, p_hash, 'staff', 'pending') RETURNING user_id INTO v_uid;

    INSERT INTO staff (user_id, fullname, position, gender, mobile_number, email)
    VALUES (v_uid, p_name, p_pos, p_gender::gender_enum, p_mobile, p_email) RETURNING staff_id INTO v_sid;

    IF p_coop_ids IS NOT NULL THEN
        FOREACH v_cid IN ARRAY p_coop_ids LOOP
            UPDATE cooperatives SET staff_id = v_sid WHERE coop_id = v_cid;
        END LOOP;
    END IF;
END; $$;


ALTER PROCEDURE public.sp_create_staff_account(IN p_hash character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying, IN p_coop_ids integer[]) OWNER TO postgres;

--
-- Name: sp_create_user_profile(character varying, character varying, public.user_role_enum, character varying, character varying, character varying, public.gender_enum, character varying, integer, integer[]); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_create_user_profile(p_username character varying, p_password_hash character varying, p_role public.user_role_enum, p_fullname character varying, p_email character varying, p_mobile_number character varying, p_gender public.gender_enum, p_position character varying, p_officer_coop_id integer DEFAULT NULL::integer, p_staff_coop_ids integer[] DEFAULT NULL::integer[]) RETURNS TABLE(new_user_id integer, new_profile_id integer, formatted_id character varying, user_role public.user_role_enum)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id INTEGER;
    v_profile_id INTEGER;
    v_formatted_id VARCHAR(10);
BEGIN
    -- 1. Create the user
    INSERT INTO users (username, password_hash, role)
    VALUES (p_username, p_password_hash, p_role)
    RETURNING user_id INTO v_user_id;

    -- 2. Create the specific profile
    CASE p_role
        WHEN 'admin'::user_role_enum THEN
            INSERT INTO admin (user_id, fullname, position, gender, mobile_number, email)
            VALUES (v_user_id, p_fullname, p_position, p_gender, p_mobile_number, p_email)
            RETURNING admin_id INTO v_profile_id;
            
            v_formatted_id := 'A' || LPAD(v_profile_id::TEXT, 3, '0');

        WHEN 'staff'::user_role_enum THEN
            INSERT INTO staff (user_id, fullname, position, gender, mobile_number, email)
            VALUES (v_user_id, p_fullname, p_position, p_gender, p_mobile_number, p_email)
            RETURNING staff_id INTO v_profile_id;
            
            v_formatted_id := 'S' || LPAD(v_profile_id::TEXT, 3, '0');
            
            -- FIX: Assign this new staff to selected cooperatives
            IF p_staff_coop_ids IS NOT NULL THEN
                UPDATE cooperatives
                SET staff_id = v_profile_id
                WHERE coop_id = ANY(p_staff_coop_ids);
            END IF;

        WHEN 'officer'::user_role_enum THEN
            INSERT INTO officers (user_id, coop_id, fullname, position, gender, mobile_number, email)
            VALUES (v_user_id, p_officer_coop_id, p_fullname, p_position, p_gender, p_mobile_number, p_email)
            RETURNING officer_id INTO v_profile_id;
            
            v_formatted_id := 'O' || LPAD(v_profile_id::TEXT, 3, '0');
    END CASE;

    -- 3. Return the new IDs
    RETURN QUERY
    SELECT v_user_id, v_profile_id, v_formatted_id, p_role;

END;
$$;


ALTER FUNCTION public.sp_create_user_profile(p_username character varying, p_password_hash character varying, p_role public.user_role_enum, p_fullname character varying, p_email character varying, p_mobile_number character varying, p_gender public.gender_enum, p_position character varying, p_officer_coop_id integer, p_staff_coop_ids integer[]) OWNER TO postgres;

--
-- Name: sp_deactivate_user(integer); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_deactivate_user(IN p_user_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE users
    SET is_active = false
    WHERE user_id = p_user_id;
END;
$$;


ALTER PROCEDURE public.sp_deactivate_user(IN p_user_id integer) OWNER TO postgres;

--
-- Name: sp_delete_cooperative(integer); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_delete_cooperative(IN _coop_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Delete dependents first due to Foreign Keys
    DELETE FROM members WHERE coop_id = _coop_id;
    DELETE FROM officers WHERE coop_id = _coop_id;
    DELETE FROM financial_data WHERE coop_id = _coop_id;
    DELETE FROM profile_data WHERE coop_id = _coop_id;
    -- Delete main record
    DELETE FROM cooperatives WHERE coop_id = _coop_id;
END;
$$;


ALTER PROCEDURE public.sp_delete_cooperative(IN _coop_id integer) OWNER TO postgres;

--
-- Name: sp_get_account_management_data(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_account_management_data() RETURNS TABLE(user_id_display text, user_id_raw integer, full_name character varying, email character varying, mobile_number character varying, role_position character varying, cooperative_name text, account_type text, gender text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    -- 1. STAFF
    SELECT 
        'S' || LPAD(s.staff_id::text, 3, '0'),
        u.user_id, s.fullname, s.email, s.mobile_number, s.position,
        COALESCE(STRING_AGG(c.cooperative_name, ', '), 'None'),
        'Staff', s.gender::text
    FROM staff s
    JOIN users u ON s.user_id = u.user_id
    LEFT JOIN cooperatives c ON c.staff_id = s.staff_id
    GROUP BY s.staff_id, u.user_id
    UNION ALL
    -- 2. OFFICERS
    SELECT 
        'O' || LPAD(o.officer_id::text, 3, '0'),
        u.user_id, o.fullname, o.email, o.mobile_number, o.position,
        c.cooperative_name,
        'Officer', o.gender::text
    FROM officers o
    JOIN users u ON o.user_id = u.user_id
    LEFT JOIN cooperatives c ON o.coop_id = c.coop_id
    UNION ALL
    -- 3. ADMINS
    SELECT 
        'A' || LPAD(a.admin_id::text, 3, '0'),
        u.user_id, a.fullname, a.email, a.mobile_number, a.position,
        '-',
        'Admin', a.gender::text
    FROM admin a
    JOIN users u ON a.user_id = u.user_id;
END;
$$;


ALTER FUNCTION public.sp_get_account_management_data() OWNER TO postgres;

--
-- Name: sp_get_all_cooperatives(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_all_cooperatives() RETURNS TABLE(coop_id integer, cooperative_name character varying, category character varying, district character varying, address character varying, mobile_number character varying, email character varying, cda_registration_number character varying, cda_registration_date date, lccdc_membership boolean, lccdc_membership_date date, operation_area character varying, business_activity character varying, board_of_directors_count integer, salaried_employees_count integer, coc_attachment_exists boolean, cote_attachment_exists boolean, assets numeric, paid_up_capital numeric, net_surplus numeric, financial_attachment_exists boolean, reporting_year integer, approval_status public.approval_status_enum, officers_count bigint, members_count bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.coop_id,
        c.cooperative_name,
        c.category,
        c.district,
        p.address,
        p.mobile_number,
        p.email_address,
        p.cda_registration_number,
        p.cda_registration_date,
        p.lccdc_membership,
        p.lccdc_membership_date,
        p.operation_area,
        p.business_activity,
        p.board_of_directors_count,
        p.salaried_employees_count,
        (p.coc_attachment IS NOT NULL) AS coc_attachment_exists,
        (p.cote_attachment IS NOT NULL) AS cote_attachment_exists,
        f.assets,
        f.paid_up_capital,
        f.net_surplus,
        (f.attachments IS NOT NULL) AS financial_attachment_exists,
        f.report_year,
        p.approval_status,
        (SELECT COUNT(*) FROM officers o WHERE o.coop_id = c.coop_id) AS officers_count,
        (SELECT COUNT(*) FROM members m WHERE m.coop_id = c.coop_id) AS members_count
    FROM cooperatives c
    LEFT JOIN profile_data p ON c.coop_id = p.coop_id
    LEFT JOIN financial_data f ON c.coop_id = f.coop_id
    ORDER BY c.cooperative_name ASC;
END;
$$;


ALTER FUNCTION public.sp_get_all_cooperatives() OWNER TO postgres;

--
-- Name: sp_get_all_profiles(character varying, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_all_profiles(p_user_role character varying, p_staff_id integer DEFAULT NULL::integer) RETURNS TABLE(coop_name character varying, address character varying, category character varying, status public.approval_status_enum, last_updated timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF p_user_role = 'admin' THEN
        RETURN QUERY 
        SELECT 
            c.cooperative_name,
            p.address,
            c.category,
            p.approval_status,
            p.updated_at
        FROM cooperatives c
        JOIN profile_data p ON c.coop_id = p.coop_id;
        
    ELSEIF p_user_role = 'staff' THEN
        RETURN QUERY 
        SELECT 
            c.cooperative_name,
            p.address,
            c.category,
            p.approval_status,
            p.updated_at
        FROM cooperatives c
        JOIN profile_data p ON c.coop_id = p.coop_id
        WHERE c.staff_id = p_staff_id;
    END IF;
END;
$$;


ALTER FUNCTION public.sp_get_all_profiles(p_user_role character varying, p_staff_id integer) OWNER TO postgres;

--
-- Name: sp_get_all_profiles_admin(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_all_profiles_admin() RETURNS TABLE(coop_id integer, cooperative_name character varying, profile_id integer, address character varying, mobile_number character varying, email_address character varying, cda_registration_number character varying, cda_registration_date date, lccdc_membership boolean, operation_area character varying, business_activity character varying, board_of_directors_count integer, salaried_employees_count integer, coc_renewal boolean, cote_renewal boolean, latest_financial_id integer, assets numeric, paid_up_capital numeric, net_surplus numeric, report_year integer, profile_updated_at timestamp with time zone)
    LANGUAGE sql
    AS $$
    SELECT
        c.coop_id,
        c.cooperative_name,
        pd.profile_id,
        pd.address,
        pd.mobile_number,
        pd.email_address,
        pd.cda_registration_number,
        pd.cda_registration_date,
        pd.lccdc_membership,
        pd.operation_area,
        pd.business_activity,
        pd.board_of_directors_count,
        pd.salaried_employees_count,
        pd.coc_renewal,
        pd.cote_renewal,
        fd.financial_id as latest_financial_id,
        fd.assets,
        fd.paid_up_capital,
        fd.net_surplus,
        fd.report_year,
        pd.updated_at as profile_updated_at
    FROM profile_data pd
    JOIN cooperatives c ON c.coop_id = pd.coop_id
    LEFT JOIN LATERAL (
        SELECT *
        FROM financial_data f
        WHERE f.coop_id = pd.coop_id
        ORDER BY f.created_at DESC
        LIMIT 1
    ) fd ON true
    ORDER BY pd.updated_at DESC;
$$;


ALTER FUNCTION public.sp_get_all_profiles_admin() OWNER TO postgres;

--
-- Name: sp_get_all_user_accounts(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_all_user_accounts(p_filter character varying DEFAULT 'active'::character varying) RETURNS TABLE(formatted_id character varying, user_id integer, profile_id integer, fullname character varying, email character varying, mobile_number character varying, "position" character varying, coop_name character varying, account_type character varying, is_active boolean, created_at timestamp with time zone, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    -- 1. Fetch STAFF
    SELECT 
        ('S' || LPAD(s.staff_id::text, 3, '0'))::VARCHAR AS formatted_id,
        s.user_id,
        s.staff_id AS profile_id,
        s.fullname,
        s.email,
        s.mobile_number,
        s.position,
        -- Aggregate all assigned coops into one string
        COALESCE(
            (SELECT STRING_AGG(c.cooperative_name, ', ') 
             FROM cooperatives c 
             WHERE c.staff_id = s.staff_id), 
            'N/A'
        )::VARCHAR AS coop_name,
        'Staff'::VARCHAR AS account_type,
        u.is_active,
        u.created_at,
        u.updated_at
    FROM staff s
    JOIN users u ON s.user_id = u.user_id
    WHERE 
        CASE 
            WHEN p_filter = 'active' THEN u.is_active = true
            WHEN p_filter = 'deactivated' THEN u.is_active = false
            ELSE true  -- 'all' or any other value
        END

    UNION ALL

    -- 2. Fetch OFFICERS
    SELECT 
        ('O' || LPAD(o.officer_id::text, 3, '0'))::VARCHAR AS formatted_id,
        o.user_id,
        o.officer_id AS profile_id,
        o.fullname,
        o.email,
        o.mobile_number,
        o.position,
        c.cooperative_name::VARCHAR AS coop_name,
        'Officer'::VARCHAR AS account_type,
        u.is_active,
        u.created_at,
        u.updated_at
    FROM officers o
    JOIN users u ON o.user_id = u.user_id
    LEFT JOIN cooperatives c ON o.coop_id = c.coop_id
    WHERE 
        CASE 
            WHEN p_filter = 'active' THEN u.is_active = true
            WHEN p_filter = 'deactivated' THEN u.is_active = false
            ELSE true  -- 'all' or any other value
        END

    UNION ALL

    -- 3. Fetch ADMINS
    SELECT 
        ('A' || LPAD(a.admin_id::text, 3, '0'))::VARCHAR AS formatted_id,
        a.user_id,
        a.admin_id AS profile_id,
        a.fullname,
        a.email,
        a.mobile_number,
        a.position,
        'N/A'::VARCHAR AS coop_name,
        'Admin'::VARCHAR AS account_type,
        u.is_active,
        u.created_at,
        u.updated_at
    FROM admin a
    JOIN users u ON a.user_id = u.user_id
    WHERE 
        CASE 
            WHEN p_filter = 'active' THEN u.is_active = true
            WHEN p_filter = 'deactivated' THEN u.is_active = false
            ELSE true  -- 'all' or any other value
        END
    
    ORDER BY created_at DESC;

END;
$$;


ALTER FUNCTION public.sp_get_all_user_accounts(p_filter character varying) OWNER TO postgres;

--
-- Name: sp_get_announcement_details(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_announcement_details(p_announcement_id integer) RETURNS TABLE(announcement_id integer, title character varying, description text, type public.announcement_type_enum, status_classification public.announcement_status_enum, scope character varying, sent_at timestamp with time zone, created_at timestamp with time zone, attachment_size integer, attachment_filename character varying, attachments_json text, sender_name character varying, sender_role character varying, coop_recipients text, officer_recipients text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_sender_name VARCHAR(100);
    v_sender_role VARCHAR(20);
    v_coop_list TEXT;
    v_officer_list TEXT;
    v_attachment_size INTEGER;
    v_attachments_json TEXT;
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

    -- Get legacy attachment size (for backward compatibility)
    SELECT 
        CASE 
            WHEN a.attachment IS NOT NULL THEN COALESCE(a.attachment_size, octet_length(a.attachment))::INTEGER
            ELSE NULL
        END
    INTO v_attachment_size
    FROM announcements a
    WHERE a.announcement_id = p_announcement_id;

    -- Get individual attachments from new table as JSON array
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'attachment_id', aa.attachment_id,
                'filename', aa.filename,
                'original_filename', aa.original_filename,
                'content_type', aa.content_type,
                'file_size', aa.file_size,
                'uploaded_at', aa.uploaded_at,
                'display_order', aa.display_order,
                'uploader_name', COALESCE(u.username, 'Unknown')
            )
            ORDER BY aa.display_order, aa.uploaded_at
        )::TEXT,
        '[]'
    )
    INTO v_attachments_json
    FROM announcement_attachments aa
    LEFT JOIN users u ON aa.uploaded_by = u.user_id
    WHERE aa.announcement_id = p_announcement_id;

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
        -- Legacy fields for backward compatibility
        COALESCE(a.attachment_size::INTEGER, v_attachment_size) AS attachment_size,
        a.attachment_filename,
        -- New individual attachments data
        v_attachments_json AS attachments_json,
        v_sender_name,
        v_sender_role,
        v_coop_list,
        v_officer_list
    FROM announcements a
    WHERE a.announcement_id = p_announcement_id;
END;
$$;


ALTER FUNCTION public.sp_get_announcement_details(p_announcement_id integer) OWNER TO postgres;

--
-- Name: FUNCTION sp_get_announcement_details(p_announcement_id integer); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.sp_get_announcement_details(p_announcement_id integer) IS 'Get detailed announcement information including recipients and attachments. 
Returns both legacy attachment fields (attachment_size, attachment_filename) for 
backward compatibility and new attachments_json field containing individual 
attachment details from the announcement_attachments table.';


--
-- Name: sp_get_announcements_by_status(public.announcement_status_enum); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_announcements_by_status(p_status public.announcement_status_enum) RETURNS TABLE(announcement_id integer, title character varying, description text, type public.announcement_type_enum, status_classification public.announcement_status_enum, scope character varying, sent_at timestamp with time zone, created_at timestamp with time zone, updated_at timestamp with time zone, creator_name character varying)
    LANGUAGE plpgsql
    AS $$
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
        COALESCE(s.fullname, adm.fullname, 'Unknown') AS creator_name
    FROM
        announcements a
    LEFT JOIN
        staff s ON a.staff_id = s.staff_id
    LEFT JOIN
        admin adm ON a.admin_id = adm.admin_id
    WHERE
        a.status_classification = p_status
    ORDER BY
        a.updated_at DESC; -- Order by most recently updated
END;
$$;


ALTER FUNCTION public.sp_get_announcements_by_status(p_status public.announcement_status_enum) OWNER TO postgres;

--
-- Name: sp_get_announcements_by_statuses(public.announcement_status_enum); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_announcements_by_statuses(p_status public.announcement_status_enum) RETURNS TABLE(announcement_id integer, title character varying, description text, type public.announcement_type_enum, status_classification public.announcement_status_enum, scope character varying, sent_at timestamp with time zone, created_at timestamp with time zone, updated_at timestamp with time zone, creator_name character varying, has_attachment boolean, attachment_count integer)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.sp_get_announcements_by_statuses(p_status public.announcement_status_enum) OWNER TO postgres;

--
-- Name: sp_get_available_coops(integer, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_available_coops(p_user_id integer, p_role character varying) RETURNS TABLE(coop_id integer, cooperative_name character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF p_role = 'admin' OR p_role = 'superuser' THEN
        -- Admin sees ALL cooperatives
        RETURN QUERY SELECT c.coop_id, c.cooperative_name FROM cooperatives c ORDER BY c.cooperative_name;
    ELSIF p_role = 'staff' THEN
        -- Staff sees ONLY cooperatives they manage
        RETURN QUERY 
        SELECT c.coop_id, c.cooperative_name 
        FROM cooperatives c 
        JOIN staff s ON c.staff_id = s.staff_id 
        WHERE s.user_id = p_user_id
        ORDER BY c.cooperative_name;
    END IF;
END;
$$;


ALTER FUNCTION public.sp_get_available_coops(p_user_id integer, p_role character varying) OWNER TO postgres;

--
-- Name: sp_get_conversation(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_conversation(p_user_a integer, p_user_b integer) RETURNS TABLE(message_id integer, sender_id integer, receiver_id integer, message text, attachment bytea, attachment_filename text, attachment_content_type text, attachment_size bigint, sent_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.sp_get_conversation(p_user_a integer, p_user_b integer) OWNER TO postgres;

--
-- Name: sp_get_mobile_by_userid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_mobile_by_userid(p_user_id integer) RETURNS character varying
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_role user_role_enum;
    v_mobile_number VARCHAR(20);
BEGIN
    -- 1. Find the user's role
    SELECT role INTO v_role FROM users WHERE user_id = p_user_id;

    -- 2. Get the mobile number from the correct table based on the role
    IF v_role = 'admin' THEN
        SELECT mobile_number INTO v_mobile_number
        FROM admin WHERE user_id = p_user_id;

    ELSIF v_role = 'staff' THEN
        SELECT mobile_number INTO v_mobile_number
        FROM staff WHERE user_id = p_user_id;

    ELSIF v_role = 'officer' THEN
        -- Use LIMIT 1 to handle cases where an officer (like 'officer_kate')
        -- might have multiple officer records. We just need one mobile number.
        SELECT mobile_number INTO v_mobile_number
        FROM officers WHERE user_id = p_user_id
        LIMIT 1;
        
    END IF;

    -- 3. Return the found number
    RETURN v_mobile_number;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
    WHEN OTHERS THEN
        -- Log error or handle as needed
        RETURN NULL;
END;
$$;


ALTER FUNCTION public.sp_get_mobile_by_userid(p_user_id integer) OWNER TO postgres;

--
-- Name: sp_get_profile_by_coop_id(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_profile_by_coop_id(p_coop_id integer) RETURNS TABLE(profile_id integer, coop_name character varying, address character varying, email character varying, assets numeric, net_surplus numeric, report_year integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.profile_id,
        c.cooperative_name,
        p.address,
        p.email_address,
        f.assets,
        f.net_surplus,
        f.report_year
    FROM cooperatives c
    LEFT JOIN profile_data p ON c.coop_id = p.coop_id
    LEFT JOIN financial_data f ON c.coop_id = f.coop_id
    WHERE c.coop_id = p_coop_id;
END;
$$;


ALTER FUNCTION public.sp_get_profile_by_coop_id(p_coop_id integer) OWNER TO postgres;

--
-- Name: sp_get_profile_per_coop_id(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_profile_per_coop_id(p_coop_id integer) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    result json;
BEGIN
    SELECT row_to_json(main)
    INTO result
    FROM (
        SELECT
            c.coop_id,
            c.cooperative_name,
            pd.*,
            fd.assets,
            fd.paid_up_capital,
            fd.net_surplus,
            fd.report_year,
            (SELECT json_agg(row_to_json(o)) FROM officers o WHERE o.coop_id = p_coop_id) AS officers,
            (SELECT json_agg(row_to_json(m)) FROM members m WHERE m.coop_id = p_coop_id) AS members
        FROM cooperatives c
        LEFT JOIN profile_data pd ON pd.coop_id = c.coop_id
        LEFT JOIN LATERAL (
            SELECT *
            FROM financial_data f
            WHERE f.coop_id = c.coop_id
            ORDER BY f.created_at DESC
            LIMIT 1
        ) fd ON true
        WHERE c.coop_id = p_coop_id
        LIMIT 1
    ) main;

    RETURN COALESCE(result, '{}'::json);
END;
$$;


ALTER FUNCTION public.sp_get_profile_per_coop_id(p_coop_id integer) OWNER TO postgres;

--
-- Name: sp_get_profiles_for_staff(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_profiles_for_staff(p_staff_id integer) RETURNS TABLE(coop_id integer, cooperative_name character varying, profile_id integer, address character varying, mobile_number character varying, email_address character varying, latest_financial_id integer, assets numeric, paid_up_capital numeric, net_surplus numeric, report_year integer, profile_updated_at timestamp with time zone)
    LANGUAGE sql
    AS $$
    SELECT
        c.coop_id,
        c.cooperative_name,
        pd.profile_id,
        pd.address,
        pd.mobile_number,
        pd.email_address,
        fd.financial_id as latest_financial_id,
        fd.assets,
        fd.paid_up_capital,
        fd.net_surplus,
        fd.report_year,
        pd.updated_at as profile_updated_at
    FROM cooperatives c
    JOIN profile_data pd ON pd.coop_id = c.coop_id
    LEFT JOIN LATERAL (
        SELECT *
        FROM financial_data f
        WHERE f.coop_id = c.coop_id
        ORDER BY f.created_at DESC
        LIMIT 1
    ) fd ON true
    WHERE c.staff_id = p_staff_id
    ORDER BY pd.updated_at DESC;
$$;


ALTER FUNCTION public.sp_get_profiles_for_staff(p_staff_id integer) OWNER TO postgres;

--
-- Name: sp_get_sms_recipients(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_sms_recipients(p_announcement_id integer) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    phone_list TEXT;
BEGIN
    WITH all_numbers AS (
        -- Get numbers from 'coop' recipients (all officers in that coop)
        SELECT o.mobile_number
        FROM officers o
        JOIN announcement_recipients ar ON o.coop_id = ar.coop_id
        WHERE ar.announcement_id = p_announcement_id
          AND o.mobile_number IS NOT NULL
          AND o.mobile_number != ''

        UNION

        -- Get numbers from specific 'officer' recipients
        SELECT o.mobile_number
        FROM officers o
        JOIN announcement_officer_recipients aor ON o.officer_id = aor.officer_id
        WHERE aor.announcement_id = p_announcement_id
          AND o.mobile_number IS NOT NULL
          AND o.mobile_number != ''
    )
    -- Aggregate all unique numbers into a single, comma-separated string
    SELECT string_agg(DISTINCT mobile_number, ',')
    INTO phone_list
    FROM all_numbers;

    RETURN phone_list;
END;
$$;


ALTER FUNCTION public.sp_get_sms_recipients(p_announcement_id integer) OWNER TO postgres;

--
-- Name: sp_get_staff_coops(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_staff_coops(p_user_id integer) RETURNS TABLE(coop_id integer, cooperative_name character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT c.coop_id, c.cooperative_name
    FROM cooperatives c
    JOIN staff s ON c.staff_id = s.staff_id
    WHERE s.user_id = p_user_id;
END;
$$;


ALTER FUNCTION public.sp_get_staff_coops(p_user_id integer) OWNER TO postgres;

--
-- Name: sp_get_user_details(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_get_user_details(p_user_id integer) RETURNS json
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_result JSON;
    v_role TEXT;
BEGIN
    -- Get user role
    SELECT role INTO v_role FROM users WHERE user_id = p_user_id;
    
    IF v_role IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Build JSON response based on role
    IF v_role = 'staff' THEN
        SELECT json_build_object(
            'user_id', u.user_id,
            'fullname', s.fullname,
            'email', s.email,
            'mobile_number', s.mobile_number,
            'gender', s.gender,
            'position', s.position,
            'role', u.role,
            'assigned_coops', COALESCE(
                (SELECT array_agg(coop_id) 
                 FROM cooperatives 
                 WHERE staff_id = s.staff_id),
                ARRAY[]::INTEGER[]
            )
        ) INTO v_result
        FROM users u
        JOIN staff s ON u.user_id = s.user_id
        WHERE u.user_id = p_user_id;
        
    ELSIF v_role = 'officer' THEN
        SELECT json_build_object(
            'user_id', u.user_id,
            'fullname', o.fullname,
            'email', o.email,
            'mobile_number', o.mobile_number,
            'gender', o.gender,
            'position', o.position,
            'role', u.role,
            'coop_id', o.coop_id
        ) INTO v_result
        FROM users u
        JOIN officers o ON u.user_id = o.user_id
        WHERE u.user_id = p_user_id;
        
    ELSIF v_role = 'admin' THEN
        SELECT json_build_object(
            'user_id', u.user_id,
            'fullname', a.fullname,
            'email', a.email,
            'mobile_number', a.mobile_number,
            'gender', a.gender,
            'position', a.position,
            'role', u.role
        ) INTO v_result
        FROM users u
        JOIN admin a ON u.user_id = a.user_id
        WHERE u.user_id = p_user_id;
    END IF;
    
    RETURN v_result;
END;
$$;


ALTER FUNCTION public.sp_get_user_details(p_user_id integer) OWNER TO postgres;

--
-- Name: sp_login_user(character varying, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_login_user(p_username character varying, p_password character varying) RETURNS public.user_login_status
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user users;
    v_is_first_login_original BOOLEAN;
    v_login_status user_login_status;
BEGIN
    -- 1. Check if username exists
    SELECT * INTO v_user FROM users WHERE username = p_username;

    IF NOT FOUND THEN
        -- User does not exist
        v_login_status := ('INVALID_USERNAME_OR_PASSWORD', NULL, NULL, NULL, NULL)::user_login_status;
        RETURN v_login_status;
    END IF;

    -- 2. Check if the password matches
    
    -- === THIS IS THE FIX ===
    -- OLD: IF v_user.password_hash = crypt(p_password, v_user.password_hash) THEN
    -- NEW:
    IF verify_pbkdf2_sha256(p_password, v_user.password_hash) THEN
    -- =======================
    
        -- Password is correct!

        -- 3. Get the original is_first_login status
        v_is_first_login_original := v_user.is_first_login;

        -- 4. If it was their first login, update the flag to false
        --    NOTE: Your trigger 'trg_auto_set_first_login' from before
        --    might make this redundant. This is fine, but good to be aware.
        IF v_is_first_login_original = TRUE THEN
            UPDATE users
            SET
                is_first_login = FALSE,
                updated_at = now()
            WHERE user_id = v_user.user_id;
        END IF;

        -- 5. Return a success status
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
$$;


ALTER FUNCTION public.sp_login_user(p_username character varying, p_password character varying) OWNER TO postgres;

--
-- Name: sp_reactivate_user(integer); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_reactivate_user(IN p_user_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validate that user exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = p_user_id) THEN
        RAISE EXCEPTION 'User with ID % not found', p_user_id;
    END IF;

    -- Check if user is already active
    IF EXISTS (SELECT 1 FROM users WHERE user_id = p_user_id AND is_active = TRUE) THEN
        RAISE EXCEPTION 'User account is already active';
    END IF;

    -- Reactivate the user
    UPDATE users
    SET is_active = TRUE
    WHERE user_id = p_user_id;

    -- Log success
    RAISE NOTICE 'User account % has been reactivated successfully', p_user_id;
    
END;
$$;


ALTER PROCEDURE public.sp_reactivate_user(IN p_user_id integer) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(128) NOT NULL,
    role public.user_role_enum NOT NULL,
    verification_status public.verification_status_enum DEFAULT 'pending'::public.verification_status_enum,
    is_first_login boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_online boolean DEFAULT false,
    last_active timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    last_login timestamp with time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: sp_register_user(character varying, character varying, public.user_role_enum); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_register_user(p_username character varying, p_password_hash character varying, p_role public.user_role_enum) RETURNS public.users
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_new_user users;
BEGIN
    INSERT INTO users (username, password_hash, role, verification_status)
    VALUES (
        p_username, 
        p_password_hash, 
        p_role,  -- No cast is needed
        'pending'
    )
    RETURNING * INTO v_new_user;

    RETURN v_new_user;

EXCEPTION
    WHEN unique_violation THEN
        RETURN NULL;
END;
$$;


ALTER FUNCTION public.sp_register_user(p_username character varying, p_password_hash character varying, p_role public.user_role_enum) OWNER TO postgres;

--
-- Name: sp_save_announcement(character varying, text, character varying, character varying, character varying, integer, character varying, integer[], integer[], integer, timestamp with time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_save_announcement(p_title character varying, p_content text, p_ann_type character varying, p_status character varying, p_scope character varying, p_creator_id integer, p_creator_role character varying, p_coop_ids integer[], p_officer_ids integer[], p_announcement_id integer DEFAULT NULL::integer, p_scheduled_time timestamp with time zone DEFAULT NULL::timestamp with time zone) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_announcement_id INTEGER;
    v_admin_id INTEGER := NULL;
    v_staff_id INTEGER := NULL;
    coop_id INTEGER;
    officer_id INTEGER;
BEGIN
    -- Get admin_id or staff_id based on role
    IF p_creator_role = 'admin' THEN
        SELECT admin_id INTO v_admin_id FROM admin WHERE user_id = p_creator_id;
    ELSIF p_creator_role = 'staff' THEN
        SELECT staff_id INTO v_staff_id FROM staff WHERE user_id = p_creator_id;
    END IF;

    -- Check if we're updating an existing announcement
    IF p_announcement_id IS NOT NULL THEN
        -- Update existing announcement
        UPDATE announcements
        SET 
            title = p_title,
            description = p_content,
            type = p_ann_type::announcement_type_enum,
            status_classification = p_status::announcement_status_enum,
            scope = p_scope,
            sent_at = CASE 
                WHEN p_status = 'scheduled' THEN p_scheduled_time
                WHEN p_status = 'sent' THEN NOW()
                ELSE sent_at
            END,
            updated_at = NOW()
        WHERE announcement_id = p_announcement_id;
        
        v_announcement_id := p_announcement_id;
        
        -- Clear existing recipients
        DELETE FROM announcement_recipients WHERE announcement_id = p_announcement_id;
        DELETE FROM announcement_officer_recipients WHERE announcement_id = p_announcement_id;
    ELSE
        -- Insert new announcement
        INSERT INTO announcements (
            admin_id, staff_id, title, description, type, 
            status_classification, scope, sent_at, created_at, updated_at
        ) VALUES (
            v_admin_id, v_staff_id, p_title, p_content, p_ann_type::announcement_type_enum,
            p_status::announcement_status_enum, p_scope,
            CASE 
                WHEN p_status = 'scheduled' THEN p_scheduled_time
                WHEN p_status = 'sent' THEN NOW()
                ELSE NULL
            END,
            NOW(), NOW()
        )
        RETURNING announcement_id INTO v_announcement_id;
    END IF;

    -- Insert cooperative recipients
    IF array_length(p_coop_ids, 1) > 0 THEN
        FOREACH coop_id IN ARRAY p_coop_ids
        LOOP
            INSERT INTO announcement_recipients (announcement_id, coop_id)
            VALUES (v_announcement_id, coop_id)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;

    -- Insert officer recipients
    IF array_length(p_officer_ids, 1) > 0 THEN
        FOREACH officer_id IN ARRAY p_officer_ids
        LOOP
            INSERT INTO announcement_officer_recipients (announcement_id, officer_id)
            VALUES (v_announcement_id, officer_id)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;

    RETURN v_announcement_id;
END;
$$;


ALTER FUNCTION public.sp_save_announcement(p_title character varying, p_content text, p_ann_type character varying, p_status character varying, p_scope character varying, p_creator_id integer, p_creator_role character varying, p_coop_ids integer[], p_officer_ids integer[], p_announcement_id integer, p_scheduled_time timestamp with time zone) OWNER TO postgres;

--
-- Name: sp_save_announcement(character varying, text, public.announcement_type_enum, public.announcement_status_enum, character varying, integer, character varying, integer[], integer[], integer, timestamp with time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_save_announcement(p_title character varying, p_content text, p_type public.announcement_type_enum, p_status public.announcement_status_enum, p_scope character varying, p_creator_id integer, p_creator_role character varying, p_coop_ids integer[], p_officer_ids integer[], p_announcement_id integer DEFAULT NULL::integer, p_scheduled_time timestamp with time zone DEFAULT NULL::timestamp with time zone) RETURNS integer
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


ALTER FUNCTION public.sp_save_announcement(p_title character varying, p_content text, p_type public.announcement_type_enum, p_status public.announcement_status_enum, p_scope character varying, p_creator_id integer, p_creator_role character varying, p_coop_ids integer[], p_officer_ids integer[], p_announcement_id integer, p_scheduled_time timestamp with time zone) OWNER TO postgres;

--
-- Name: sp_send_message(integer, integer, text, bytea, text, text, bigint); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_send_message(p_sender_id integer, p_receiver_id integer, p_message text, p_attachment bytea DEFAULT NULL::bytea, p_attachment_filename text DEFAULT NULL::text, p_attachment_content_type text DEFAULT NULL::text, p_attachment_size bigint DEFAULT NULL::bigint) RETURNS TABLE(message_id integer, sender_id integer, receiver_id integer, message text, attachment bytea, attachment_filename text, attachment_content_type text, attachment_size bigint, sent_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.sp_send_message(p_sender_id integer, p_receiver_id integer, p_message text, p_attachment bytea, p_attachment_filename text, p_attachment_content_type text, p_attachment_size bigint) OWNER TO postgres;

--
-- Name: sp_update_account_details(integer, character varying, character varying, character varying, character varying, character varying, character varying); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_update_account_details(IN p_user_id integer, IN p_role character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Update Base User (Username = Email)
    UPDATE users SET username = p_email, updated_at = now() WHERE user_id = p_user_id;

    -- Update Profile
    IF p_role = 'staff' THEN
        UPDATE staff SET fullname=p_name, position=p_pos, gender=p_gender::gender_enum, mobile_number=p_mobile, email=p_email WHERE user_id=p_user_id;
    ELSIF p_role = 'officer' THEN
        UPDATE officers SET fullname=p_name, position=p_pos, gender=p_gender::gender_enum, mobile_number=p_mobile, email=p_email WHERE user_id=p_user_id;
    ELSIF p_role = 'admin' THEN
        UPDATE admin SET fullname=p_name, position=p_pos, gender=p_gender::gender_enum, mobile_number=p_mobile, email=p_email WHERE user_id=p_user_id;
    END IF;
END; $$;


ALTER PROCEDURE public.sp_update_account_details(IN p_user_id integer, IN p_role character varying, IN p_name character varying, IN p_pos character varying, IN p_gender character varying, IN p_mobile character varying, IN p_email character varying) OWNER TO postgres;

--
-- Name: sp_update_cooperative_profile(integer, character varying, character varying, character varying, numeric, numeric, numeric); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_update_cooperative_profile(IN _coop_id integer, IN _address character varying, IN _mobile character varying, IN _email character varying, IN _assets numeric, IN _capital numeric, IN _surplus numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Update Profile
    UPDATE profile_data 
    SET address = _address, 
        mobile_number = _mobile, 
        email_address = _email,
        updated_at = NOW()
    WHERE coop_id = _coop_id;

    -- Update Financials
    UPDATE financial_data
    SET assets = _assets,
        paid_up_capital = _capital,
        net_surplus = _surplus,
        updated_at = NOW()
    WHERE coop_id = _coop_id;
END;
$$;


ALTER PROCEDURE public.sp_update_cooperative_profile(IN _coop_id integer, IN _address character varying, IN _mobile character varying, IN _email character varying, IN _assets numeric, IN _capital numeric, IN _surplus numeric) OWNER TO postgres;

--
-- Name: sp_update_user_profile(integer, character varying, character varying, character varying, character varying, character varying, integer, integer[]); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_update_user_profile(IN p_user_id integer, IN p_fullname character varying, IN p_email character varying, IN p_mobile_number character varying, IN p_gender character varying, IN p_position character varying, IN p_officer_coop_id integer DEFAULT NULL::integer, IN p_staff_coop_ids integer[] DEFAULT NULL::integer[])
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_role user_role_enum;
    v_staff_id INTEGER;
    v_gender_enum gender_enum;
BEGIN
    -- Cast string gender to enum
    v_gender_enum := CASE 
        WHEN p_gender IS NOT NULL THEN p_gender::gender_enum 
        ELSE NULL 
    END;

    -- Get the user's role
    SELECT role INTO v_role FROM users WHERE user_id = p_user_id;

    -- Update the username (email)
    UPDATE users SET username = p_email, updated_at = NOW() WHERE user_id = p_user_id;

    -- Update the specific profile
    IF v_role = 'admin'::user_role_enum THEN
        UPDATE admin
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position
        WHERE user_id = p_user_id;
        
    ELSIF v_role = 'staff'::user_role_enum THEN
        UPDATE staff
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position
        WHERE user_id = p_user_id
        RETURNING staff_id INTO v_staff_id;
        
        -- Un-assign all current coops from this staff
        UPDATE cooperatives SET staff_id = NULL WHERE staff_id = v_staff_id;
        
        -- Re-assign the new list of coops
        IF p_staff_coop_ids IS NOT NULL AND array_length(p_staff_coop_ids, 1) > 0 THEN
            UPDATE cooperatives
            SET staff_id = v_staff_id
            WHERE coop_id = ANY(p_staff_coop_ids);
        END IF;

    ELSIF v_role = 'officer'::user_role_enum THEN
        UPDATE officers
        SET fullname = p_fullname, 
            email = p_email, 
            mobile_number = p_mobile_number, 
            gender = v_gender_enum, 
            "position" = p_position, 
            coop_id = p_officer_coop_id
        WHERE user_id = p_user_id;
    END IF;

END;
$$;


ALTER PROCEDURE public.sp_update_user_profile(IN p_user_id integer, IN p_fullname character varying, IN p_email character varying, IN p_mobile_number character varying, IN p_gender character varying, IN p_position character varying, IN p_officer_coop_id integer, IN p_staff_coop_ids integer[]) OWNER TO postgres;

--
-- Name: trg_update_first_login_status(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_update_first_login_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check the NEW value of verification_status being saved
    -- This 'NEW' variable is special syntax for triggers
    IF NEW.verification_status = 'verified' THEN
        NEW.is_first_login := false;
    ELSIF NEW.verification_status = 'pending' THEN
        NEW.is_first_login := true;
    END IF;
    
    -- Always return the (possibly modified) NEW row to be saved
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_update_first_login_status() OWNER TO postgres;

--
-- Name: verify_pbkdf2_sha256(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.verify_pbkdf2_sha256(p_password text, p_django_hash text) RETURNS boolean
    LANGUAGE plpython3u
    AS $_$
    # We are writing Python code inside PostgreSQL
    import hashlib
    import base64

    try:
        # 1. Parse the Django hash string
        # e.g., 'pbkdf2_sha256$1000000$salt$hash'
        algo, iterations, salt, stored_hash_b64 = p_django_hash.split('$', 3)
        
        if algo != 'pbkdf2_sha256':
            return False
        
        iterations = int(iterations)
        
        # 2. Decode the stored hash from Base64
        stored_hash_bytes = base64.b64decode(stored_hash_b64)
        
        # 3. Calculate the new hash using the same parameters
        new_hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            p_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations,
            dklen=len(stored_hash_bytes) # Get the exact length (e.g., 32 bytes)
        )
        
        # 4. Compare the two byte arrays
        return new_hash_bytes == stored_hash_bytes
        
    except Exception:
        # If splitting fails, hash is invalid, etc.
        return False
$_$;


ALTER FUNCTION public.verify_pbkdf2_sha256(p_password text, p_django_hash text) OWNER TO postgres;

--
-- Name: activity_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.activity_logs (
    activity_id integer NOT NULL,
    coop_id integer,
    user_id integer,
    action_type character varying(50) NOT NULL,
    description text NOT NULL,
    user_fullname character varying(100),
    user_organization character varying(200),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.activity_logs OWNER TO postgres;

--
-- Name: activity_logs_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.activity_logs_activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.activity_logs_activity_id_seq OWNER TO postgres;

--
-- Name: activity_logs_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.activity_logs_activity_id_seq OWNED BY public.activity_logs.activity_id;


--
-- Name: admin; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin (
    admin_id integer NOT NULL,
    user_id integer NOT NULL,
    fullname character varying(100),
    "position" character varying(50),
    gender public.gender_enum,
    mobile_number character varying(20),
    email character varying(100)
);


ALTER TABLE public.admin OWNER TO postgres;

--
-- Name: admin_admin_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.admin_admin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_admin_id_seq OWNER TO postgres;

--
-- Name: admin_admin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.admin_admin_id_seq OWNED BY public.admin.admin_id;


--
-- Name: announcement_attachments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.announcement_attachments (
    attachment_id integer NOT NULL,
    announcement_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    content_type character varying(100) NOT NULL,
    file_size bigint NOT NULL,
    file_data bytea NOT NULL,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    uploaded_by integer,
    display_order integer DEFAULT 0
);


ALTER TABLE public.announcement_attachments OWNER TO postgres;

--
-- Name: TABLE announcement_attachments; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.announcement_attachments IS 'Stores individual attachments for announcements';


--
-- Name: COLUMN announcement_attachments.attachment_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.attachment_id IS 'Primary key for attachments';


--
-- Name: COLUMN announcement_attachments.announcement_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.announcement_id IS 'Foreign key to announcements table';


--
-- Name: COLUMN announcement_attachments.filename; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.filename IS 'Stored filename';


--
-- Name: COLUMN announcement_attachments.original_filename; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.original_filename IS 'Original filename from upload';


--
-- Name: COLUMN announcement_attachments.content_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.content_type IS 'MIME type of the file';


--
-- Name: COLUMN announcement_attachments.file_size; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.file_size IS 'Size of file in bytes';


--
-- Name: COLUMN announcement_attachments.file_data; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.file_data IS 'Binary file data';


--
-- Name: COLUMN announcement_attachments.uploaded_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.uploaded_at IS 'Timestamp when file was uploaded';


--
-- Name: COLUMN announcement_attachments.uploaded_by; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.uploaded_by IS 'User who uploaded the file';


--
-- Name: COLUMN announcement_attachments.display_order; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.announcement_attachments.display_order IS 'Order for displaying multiple attachments';


--
-- Name: announcement_attachments_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.announcement_attachments_attachment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.announcement_attachments_attachment_id_seq OWNER TO postgres;

--
-- Name: announcement_attachments_attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.announcement_attachments_attachment_id_seq OWNED BY public.announcement_attachments.attachment_id;


--
-- Name: announcement_officer_recipients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.announcement_officer_recipients (
    announcement_id integer NOT NULL,
    officer_id integer NOT NULL
);


ALTER TABLE public.announcement_officer_recipients OWNER TO postgres;

--
-- Name: announcement_recipients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.announcement_recipients (
    announcement_id integer NOT NULL,
    coop_id integer NOT NULL
);


ALTER TABLE public.announcement_recipients OWNER TO postgres;

--
-- Name: announcements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.announcements (
    announcement_id integer NOT NULL,
    staff_id integer,
    admin_id integer,
    description text,
    type public.announcement_type_enum,
    attachment bytea,
    sent_at timestamp with time zone,
    scope character varying(50),
    title character varying(200),
    status_classification public.announcement_status_enum DEFAULT 'draft'::public.announcement_status_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    attachment_filename character varying(255),
    attachment_content_type character varying(255),
    attachment_size bigint,
    CONSTRAINT announcement_sender_check CHECK ((((staff_id IS NOT NULL) AND (admin_id IS NULL)) OR ((staff_id IS NULL) AND (admin_id IS NOT NULL))))
);


ALTER TABLE public.announcements OWNER TO postgres;

--
-- Name: announcements_announcement_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.announcements_announcement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.announcements_announcement_id_seq OWNER TO postgres;

--
-- Name: announcements_announcement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.announcements_announcement_id_seq OWNED BY public.announcements.announcement_id;


--
-- Name: app_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_events (
    id bigint NOT NULL,
    title character varying(255) NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    description text,
    user_id integer
);


ALTER TABLE public.app_events OWNER TO postgres;

--
-- Name: app_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.app_events ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.app_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO postgres;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO postgres;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO postgres;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cache_table; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cache_table (
    cache_key character varying(255) NOT NULL,
    value text NOT NULL,
    expires timestamp with time zone NOT NULL
);


ALTER TABLE public.cache_table OWNER TO postgres;

--
-- Name: cooperatives; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cooperatives (
    coop_id integer NOT NULL,
    staff_id integer,
    cooperative_name character varying(200) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    category character varying(255),
    district character varying(255),
    is_active boolean DEFAULT true
);


ALTER TABLE public.cooperatives OWNER TO postgres;

--
-- Name: COLUMN cooperatives.is_active; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.cooperatives.is_active IS 'Soft delete flag: TRUE = active, FALSE = deactivated, NULL = not set';


--
-- Name: cooperatives_coop_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cooperatives_coop_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cooperatives_coop_id_seq OWNER TO postgres;

--
-- Name: cooperatives_coop_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cooperatives_coop_id_seq OWNED BY public.cooperatives.coop_id;


--
-- Name: databank_ocrscansession; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.databank_ocrscansession (
    id bigint NOT NULL,
    image character varying(100),
    extracted_text text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    is_consumed boolean NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.databank_ocrscansession OWNER TO postgres;

--
-- Name: databank_ocrscansession_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.databank_ocrscansession ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.databank_ocrscansession_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: financial_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_data (
    financial_id integer NOT NULL,
    coop_id integer NOT NULL,
    assets numeric(20,2) DEFAULT 0,
    paid_up_capital numeric(20,2) DEFAULT 0,
    net_surplus numeric(20,2) DEFAULT 0,
    attachments bytea,
    approval_status public.approval_status_enum,
    report_year integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT financial_data_report_year_check CHECK (((report_year >= 1900) AND ((report_year)::numeric <= (EXTRACT(year FROM now()) + (1)::numeric))))
);


ALTER TABLE public.financial_data OWNER TO postgres;

--
-- Name: financial_data_financial_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.financial_data_financial_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.financial_data_financial_id_seq OWNER TO postgres;

--
-- Name: financial_data_financial_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.financial_data_financial_id_seq OWNED BY public.financial_data.financial_id;


--
-- Name: members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.members (
    member_id integer NOT NULL,
    coop_id integer NOT NULL,
    fullname character varying(100) NOT NULL,
    gender public.gender_enum,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    mobile_number character varying(20)
);


ALTER TABLE public.members OWNER TO postgres;

--
-- Name: members_member_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.members_member_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.members_member_id_seq OWNER TO postgres;

--
-- Name: members_member_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.members_member_id_seq OWNED BY public.members.member_id;


--
-- Name: message_recipients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.message_recipients (
    message_id integer NOT NULL,
    receiver_id integer NOT NULL,
    received_at timestamp with time zone,
    status character varying(20) DEFAULT 'sent'::character varying,
    seen_at timestamp with time zone
);


ALTER TABLE public.message_recipients OWNER TO postgres;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    message_id integer NOT NULL,
    sender_id integer,
    message text NOT NULL,
    sent_at timestamp with time zone DEFAULT now() NOT NULL,
    attachment bytea,
    attachment_filename character varying(255),
    attachment_content_type character varying(255),
    attachment_size bigint
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: messages_message_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messages_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_message_id_seq OWNER TO postgres;

--
-- Name: messages_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messages_message_id_seq OWNED BY public.messages.message_id;


--
-- Name: messenger_conversations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messenger_conversations (
    conversation_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.messenger_conversations OWNER TO postgres;

--
-- Name: messenger_conversations_conversation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messenger_conversations_conversation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messenger_conversations_conversation_id_seq OWNER TO postgres;

--
-- Name: messenger_conversations_conversation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messenger_conversations_conversation_id_seq OWNED BY public.messenger_conversations.conversation_id;


--
-- Name: messenger_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messenger_messages (
    message_id integer NOT NULL,
    conversation_id integer NOT NULL,
    sender_id integer NOT NULL,
    message_text text,
    attachment bytea,
    attachment_filename character varying(255),
    attachment_content_type character varying(255),
    attachment_size bigint,
    sent_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.messenger_messages OWNER TO postgres;

--
-- Name: messenger_messages_message_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messenger_messages_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messenger_messages_message_id_seq OWNER TO postgres;

--
-- Name: messenger_messages_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messenger_messages_message_id_seq OWNED BY public.messenger_messages.message_id;


--
-- Name: messenger_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messenger_participants (
    participant_id integer NOT NULL,
    conversation_id integer NOT NULL,
    user_id integer NOT NULL,
    last_read_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.messenger_participants OWNER TO postgres;

--
-- Name: messenger_participants_participant_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messenger_participants_participant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messenger_participants_participant_id_seq OWNER TO postgres;

--
-- Name: messenger_participants_participant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messenger_participants_participant_id_seq OWNED BY public.messenger_participants.participant_id;


--
-- Name: officers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.officers (
    officer_id integer NOT NULL,
    user_id integer,
    coop_id integer NOT NULL,
    fullname character varying(100),
    "position" character varying(50),
    gender public.gender_enum,
    mobile_number character varying(20),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    email character varying(100)
);


ALTER TABLE public.officers OWNER TO postgres;

--
-- Name: officers_officer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.officers_officer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.officers_officer_id_seq OWNER TO postgres;

--
-- Name: officers_officer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.officers_officer_id_seq OWNED BY public.officers.officer_id;


--
-- Name: profile_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.profile_data (
    profile_id integer NOT NULL,
    coop_id integer NOT NULL,
    address character varying(255),
    mobile_number character varying(20),
    email_address character varying(100),
    cda_registration_number character varying(100),
    cda_registration_date date,
    lccdc_membership boolean,
    lccdc_membership_date date,
    operation_area character varying(100),
    business_activity character varying(100),
    board_of_directors_count integer,
    salaried_employees_count integer,
    coc_renewal boolean,
    cote_renewal boolean,
    coc_attachment bytea,
    cote_attachment bytea,
    approval_status public.approval_status_enum,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    report_year integer
);


ALTER TABLE public.profile_data OWNER TO postgres;

--
-- Name: profile_data_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.profile_data_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.profile_data_profile_id_seq OWNER TO postgres;

--
-- Name: profile_data_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.profile_data_profile_id_seq OWNED BY public.profile_data.profile_id;


--
-- Name: staff; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.staff (
    staff_id integer NOT NULL,
    user_id integer NOT NULL,
    fullname character varying(100),
    "position" character varying(50),
    gender public.gender_enum,
    mobile_number character varying(20),
    email character varying(100)
);


ALTER TABLE public.staff OWNER TO postgres;

--
-- Name: staff_staff_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.staff_staff_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.staff_staff_id_seq OWNER TO postgres;

--
-- Name: staff_staff_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.staff_staff_id_seq OWNED BY public.staff.staff_id;


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: webpush_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.webpush_group (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE public.webpush_group OWNER TO postgres;

--
-- Name: webpush_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.webpush_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.webpush_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: webpush_pushinformation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.webpush_pushinformation (
    id integer NOT NULL,
    group_id integer,
    subscription_id integer NOT NULL,
    user_id integer
);


ALTER TABLE public.webpush_pushinformation OWNER TO postgres;

--
-- Name: webpush_pushinformation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.webpush_pushinformation ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.webpush_pushinformation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: webpush_subscriptioninfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.webpush_subscriptioninfo (
    id integer NOT NULL,
    browser character varying(100) NOT NULL,
    endpoint character varying(500) NOT NULL,
    auth character varying(100) NOT NULL,
    p256dh character varying(100) NOT NULL,
    user_agent character varying(500) NOT NULL
);


ALTER TABLE public.webpush_subscriptioninfo OWNER TO postgres;

--
-- Name: webpush_subscriptioninfo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.webpush_subscriptioninfo ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.webpush_subscriptioninfo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: activity_logs activity_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_logs ALTER COLUMN activity_id SET DEFAULT nextval('public.activity_logs_activity_id_seq'::regclass);


--
-- Name: admin admin_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin ALTER COLUMN admin_id SET DEFAULT nextval('public.admin_admin_id_seq'::regclass);


--
-- Name: announcement_attachments attachment_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_attachments ALTER COLUMN attachment_id SET DEFAULT nextval('public.announcement_attachments_attachment_id_seq'::regclass);


--
-- Name: announcements announcement_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcements ALTER COLUMN announcement_id SET DEFAULT nextval('public.announcements_announcement_id_seq'::regclass);


--
-- Name: cooperatives coop_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cooperatives ALTER COLUMN coop_id SET DEFAULT nextval('public.cooperatives_coop_id_seq'::regclass);


--
-- Name: financial_data financial_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_data ALTER COLUMN financial_id SET DEFAULT nextval('public.financial_data_financial_id_seq'::regclass);


--
-- Name: members member_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.members ALTER COLUMN member_id SET DEFAULT nextval('public.members_member_id_seq'::regclass);


--
-- Name: messages message_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages ALTER COLUMN message_id SET DEFAULT nextval('public.messages_message_id_seq'::regclass);


--
-- Name: messenger_conversations conversation_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_conversations ALTER COLUMN conversation_id SET DEFAULT nextval('public.messenger_conversations_conversation_id_seq'::regclass);


--
-- Name: messenger_messages message_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_messages ALTER COLUMN message_id SET DEFAULT nextval('public.messenger_messages_message_id_seq'::regclass);


--
-- Name: messenger_participants participant_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_participants ALTER COLUMN participant_id SET DEFAULT nextval('public.messenger_participants_participant_id_seq'::regclass);


--
-- Name: officers officer_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officers ALTER COLUMN officer_id SET DEFAULT nextval('public.officers_officer_id_seq'::regclass);


--
-- Name: profile_data profile_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profile_data ALTER COLUMN profile_id SET DEFAULT nextval('public.profile_data_profile_id_seq'::regclass);


--
-- Name: staff staff_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff ALTER COLUMN staff_id SET DEFAULT nextval('public.staff_staff_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (activity_id);


--
-- Name: admin admin_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin
    ADD CONSTRAINT admin_email_key UNIQUE (email);


--
-- Name: admin admin_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin
    ADD CONSTRAINT admin_pkey PRIMARY KEY (admin_id);


--
-- Name: admin admin_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin
    ADD CONSTRAINT admin_user_id_key UNIQUE (user_id);


--
-- Name: announcement_attachments announcement_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_attachments
    ADD CONSTRAINT announcement_attachments_pkey PRIMARY KEY (attachment_id);


--
-- Name: announcement_officer_recipients announcement_officer_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_officer_recipients
    ADD CONSTRAINT announcement_officer_recipients_pkey PRIMARY KEY (announcement_id, officer_id);


--
-- Name: announcement_recipients announcement_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_recipients
    ADD CONSTRAINT announcement_recipients_pkey PRIMARY KEY (announcement_id, coop_id);


--
-- Name: announcements announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcements
    ADD CONSTRAINT announcements_pkey PRIMARY KEY (announcement_id);


--
-- Name: app_events app_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT app_events_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: cache_table cache_table_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cache_table
    ADD CONSTRAINT cache_table_pkey PRIMARY KEY (cache_key);


--
-- Name: cooperatives cooperatives_cooperative_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cooperatives
    ADD CONSTRAINT cooperatives_cooperative_name_key UNIQUE (cooperative_name);


--
-- Name: cooperatives cooperatives_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cooperatives
    ADD CONSTRAINT cooperatives_pkey PRIMARY KEY (coop_id);


--
-- Name: databank_ocrscansession databank_ocrscansession_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.databank_ocrscansession
    ADD CONSTRAINT databank_ocrscansession_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: financial_data financial_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_data
    ADD CONSTRAINT financial_data_pkey PRIMARY KEY (financial_id);


--
-- Name: members members_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.members
    ADD CONSTRAINT members_pkey PRIMARY KEY (member_id);


--
-- Name: message_recipients message_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message_recipients
    ADD CONSTRAINT message_recipients_pkey PRIMARY KEY (message_id, receiver_id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (message_id);


--
-- Name: messenger_conversations messenger_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_conversations
    ADD CONSTRAINT messenger_conversations_pkey PRIMARY KEY (conversation_id);


--
-- Name: messenger_messages messenger_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_messages
    ADD CONSTRAINT messenger_messages_pkey PRIMARY KEY (message_id);


--
-- Name: messenger_participants messenger_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_participants
    ADD CONSTRAINT messenger_participants_pkey PRIMARY KEY (participant_id);


--
-- Name: officers officers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officers
    ADD CONSTRAINT officers_pkey PRIMARY KEY (officer_id);


--
-- Name: profile_data profile_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profile_data
    ADD CONSTRAINT profile_data_pkey PRIMARY KEY (profile_id);


--
-- Name: staff staff_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_email_key UNIQUE (email);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (staff_id);


--
-- Name: staff staff_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_user_id_key UNIQUE (user_id);


--
-- Name: messenger_participants uniq_messenger_participant; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_participants
    ADD CONSTRAINT uniq_messenger_participant UNIQUE (conversation_id, user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: webpush_group webpush_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_group
    ADD CONSTRAINT webpush_group_name_key UNIQUE (name);


--
-- Name: webpush_group webpush_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_group
    ADD CONSTRAINT webpush_group_pkey PRIMARY KEY (id);


--
-- Name: webpush_pushinformation webpush_pushinformation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_pushinformation
    ADD CONSTRAINT webpush_pushinformation_pkey PRIMARY KEY (id);


--
-- Name: webpush_subscriptioninfo webpush_subscriptioninfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_subscriptioninfo
    ADD CONSTRAINT webpush_subscriptioninfo_pkey PRIMARY KEY (id);


--
-- Name: app_events_user_id_ad999e37; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX app_events_user_id_ad999e37 ON public.app_events USING btree (user_id);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: cache_table_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cache_table_expires ON public.cache_table USING btree (expires);


--
-- Name: databank_ocrscansession_user_id_25393917; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX databank_ocrscansession_user_id_25393917 ON public.databank_ocrscansession USING btree (user_id);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: idx_activity_logs_coop_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_activity_logs_coop_id ON public.activity_logs USING btree (coop_id);


--
-- Name: idx_activity_logs_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_activity_logs_created_at ON public.activity_logs USING btree (created_at DESC);


--
-- Name: idx_announcement_attachments_announcement; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_announcement_attachments_announcement ON public.announcement_attachments USING btree (announcement_id);


--
-- Name: idx_announcement_attachments_uploaded_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_announcement_attachments_uploaded_at ON public.announcement_attachments USING btree (uploaded_at);


--
-- Name: idx_announcement_officer_recipients_officer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_announcement_officer_recipients_officer_id ON public.announcement_officer_recipients USING btree (officer_id);


--
-- Name: idx_cooperatives_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cooperatives_is_active ON public.cooperatives USING btree (is_active);


--
-- Name: idx_financial_coop_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_financial_coop_id ON public.financial_data USING btree (coop_id);


--
-- Name: idx_members_coop_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_members_coop_id ON public.members USING btree (coop_id);


--
-- Name: idx_messenger_conversations_updated; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messenger_conversations_updated ON public.messenger_conversations USING btree (updated_at DESC);


--
-- Name: idx_messenger_cp_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messenger_cp_user ON public.messenger_participants USING btree (user_id);


--
-- Name: idx_messenger_msg_conv; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messenger_msg_conv ON public.messenger_messages USING btree (conversation_id);


--
-- Name: idx_officers_coop_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_officers_coop_id ON public.officers USING btree (coop_id);


--
-- Name: idx_profile_coop_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_profile_coop_id ON public.profile_data USING btree (coop_id);


--
-- Name: idx_profile_coop_year; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_profile_coop_year ON public.profile_data USING btree (coop_id, report_year);


--
-- Name: idx_profile_report_year; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_profile_report_year ON public.profile_data USING btree (report_year);


--
-- Name: profile_data_coop_null_year_unique; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX profile_data_coop_null_year_unique ON public.profile_data USING btree (coop_id) WHERE (report_year IS NULL);


--
-- Name: profile_data_coop_year_unique; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX profile_data_coop_year_unique ON public.profile_data USING btree (coop_id, report_year) WHERE (report_year IS NOT NULL);


--
-- Name: webpush_group_name_55a9d24d_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX webpush_group_name_55a9d24d_like ON public.webpush_group USING btree (name varchar_pattern_ops);


--
-- Name: webpush_pushinformation_group_id_262dcc9a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX webpush_pushinformation_group_id_262dcc9a ON public.webpush_pushinformation USING btree (group_id);


--
-- Name: webpush_pushinformation_subscription_id_7989aa34; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX webpush_pushinformation_subscription_id_7989aa34 ON public.webpush_pushinformation USING btree (subscription_id);


--
-- Name: webpush_pushinformation_user_id_5e083b7f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX webpush_pushinformation_user_id_5e083b7f ON public.webpush_pushinformation USING btree (user_id);


--
-- Name: users trg_auto_set_first_login; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auto_set_first_login BEFORE INSERT OR UPDATE OF verification_status ON public.users FOR EACH ROW EXECUTE FUNCTION public.trg_update_first_login_status();


--
-- Name: announcements trg_set_announcements_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_set_announcements_timestamp BEFORE UPDATE ON public.announcements FOR EACH ROW EXECUTE FUNCTION public.fn_trigger_set_timestamp();


--
-- Name: messenger_messages trg_update_messenger_ts; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_messenger_ts AFTER INSERT ON public.messenger_messages FOR EACH ROW EXECUTE FUNCTION public.fn_update_messenger_timestamp();


--
-- Name: activity_logs activity_logs_coop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_coop_id_fkey FOREIGN KEY (coop_id) REFERENCES public.cooperatives(coop_id) ON DELETE CASCADE;


--
-- Name: activity_logs activity_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: admin admin_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin
    ADD CONSTRAINT admin_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: announcement_officer_recipients announcement_officer_recipients_announcement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_officer_recipients
    ADD CONSTRAINT announcement_officer_recipients_announcement_id_fkey FOREIGN KEY (announcement_id) REFERENCES public.announcements(announcement_id) ON DELETE CASCADE;


--
-- Name: announcement_officer_recipients announcement_officer_recipients_officer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_officer_recipients
    ADD CONSTRAINT announcement_officer_recipients_officer_id_fkey FOREIGN KEY (officer_id) REFERENCES public.officers(officer_id) ON DELETE CASCADE;


--
-- Name: announcement_recipients announcement_recipients_announcement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_recipients
    ADD CONSTRAINT announcement_recipients_announcement_id_fkey FOREIGN KEY (announcement_id) REFERENCES public.announcements(announcement_id) ON DELETE CASCADE;


--
-- Name: announcement_recipients announcement_recipients_coop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_recipients
    ADD CONSTRAINT announcement_recipients_coop_id_fkey FOREIGN KEY (coop_id) REFERENCES public.cooperatives(coop_id) ON DELETE CASCADE;


--
-- Name: announcements announcements_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcements
    ADD CONSTRAINT announcements_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.admin(admin_id) ON DELETE SET NULL;


--
-- Name: announcements announcements_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcements
    ADD CONSTRAINT announcements_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(staff_id) ON DELETE SET NULL;


--
-- Name: app_events app_events_user_id_ad999e37_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT app_events_user_id_ad999e37_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cooperatives cooperatives_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cooperatives
    ADD CONSTRAINT cooperatives_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(staff_id);


--
-- Name: databank_ocrscansession databank_ocrscansession_user_id_25393917_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.databank_ocrscansession
    ADD CONSTRAINT databank_ocrscansession_user_id_25393917_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: financial_data financial_data_coop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_data
    ADD CONSTRAINT financial_data_coop_id_fkey FOREIGN KEY (coop_id) REFERENCES public.cooperatives(coop_id) ON DELETE CASCADE;


--
-- Name: announcement_attachments fk_announcement_attachment_announcement; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_attachments
    ADD CONSTRAINT fk_announcement_attachment_announcement FOREIGN KEY (announcement_id) REFERENCES public.announcements(announcement_id) ON DELETE CASCADE;


--
-- Name: announcement_attachments fk_announcement_attachment_uploader; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.announcement_attachments
    ADD CONSTRAINT fk_announcement_attachment_uploader FOREIGN KEY (uploaded_by) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: messenger_participants fk_messenger_cp_conv; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_participants
    ADD CONSTRAINT fk_messenger_cp_conv FOREIGN KEY (conversation_id) REFERENCES public.messenger_conversations(conversation_id) ON DELETE CASCADE;


--
-- Name: messenger_participants fk_messenger_cp_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_participants
    ADD CONSTRAINT fk_messenger_cp_user FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: messenger_messages fk_messenger_msg_conv; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_messages
    ADD CONSTRAINT fk_messenger_msg_conv FOREIGN KEY (conversation_id) REFERENCES public.messenger_conversations(conversation_id) ON DELETE CASCADE;


--
-- Name: messenger_messages fk_messenger_msg_sender; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messenger_messages
    ADD CONSTRAINT fk_messenger_msg_sender FOREIGN KEY (sender_id) REFERENCES public.users(user_id);


--
-- Name: members members_coop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.members
    ADD CONSTRAINT members_coop_id_fkey FOREIGN KEY (coop_id) REFERENCES public.cooperatives(coop_id) ON DELETE CASCADE;


--
-- Name: message_recipients message_recipients_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message_recipients
    ADD CONSTRAINT message_recipients_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(message_id) ON DELETE CASCADE;


--
-- Name: message_recipients message_recipients_receiver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message_recipients
    ADD CONSTRAINT message_recipients_receiver_id_fkey FOREIGN KEY (receiver_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: officers officers_coop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officers
    ADD CONSTRAINT officers_coop_id_fkey FOREIGN KEY (coop_id) REFERENCES public.cooperatives(coop_id) ON DELETE CASCADE;


--
-- Name: officers officers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officers
    ADD CONSTRAINT officers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: profile_data profile_data_coop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profile_data
    ADD CONSTRAINT profile_data_coop_id_fkey FOREIGN KEY (coop_id) REFERENCES public.cooperatives(coop_id) ON DELETE CASCADE;


--
-- Name: staff staff_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: webpush_pushinformation webpush_pushinformation_group_id_262dcc9a_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_pushinformation
    ADD CONSTRAINT webpush_pushinformation_group_id_262dcc9a_fk FOREIGN KEY (group_id) REFERENCES public.webpush_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webpush_pushinformation webpush_pushinformation_subscription_id_7989aa34_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_pushinformation
    ADD CONSTRAINT webpush_pushinformation_subscription_id_7989aa34_fk FOREIGN KEY (subscription_id) REFERENCES public.webpush_subscriptioninfo(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webpush_pushinformation webpush_pushinformation_user_id_5e083b7f_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webpush_pushinformation
    ADD CONSTRAINT webpush_pushinformation_user_id_5e083b7f_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict zNxxTyp9rMInyJr9OKMGOe0LSnYst7xtVAfMx8Zgsm1IrmpXdXGv8aC8gVwUdCa

