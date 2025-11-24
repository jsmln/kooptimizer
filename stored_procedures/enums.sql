CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other', 'others');
CREATE TYPE user_role_enum AS ENUM ('admin', 'staff', 'officer');
CREATE TYPE verification_status_enum AS ENUM ('pending', 'verified');
CREATE TYPE announcement_type_enum AS ENUM ('sms', 'email');
CREATE TYPE announcement_status_enum AS ENUM ('draft', 'sent', 'scheduled');