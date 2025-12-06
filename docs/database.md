# Database: schema and migrations

This document describes the database approach for the Kooptimizer project, where to find migration scripts, how to run them, and detailed instructions for setting up the database using `db/schema.sql`.

Overview
--------
- The project uses Django ORM for model definitions and Django migrations for schema evolution.
- Migrations are present under each app's `migrations/` folder (e.g. `apps/users/migrations`).
- The `database/` directory contains backups, dumps, and some environment-specific artifacts. Many of those files are sensitive or environment-specific; the repository `.gitignore` excludes them by default.
- **`db/schema.sql`** contains the complete database schema export (147 KB) including 34 tables, 39 functions, 10 stored procedures, 7 custom types/enums, 37 indexes, and all constraints.

Setting up database using schema.sql
------------------------------------

### Fresh database setup (recommended for new installations)

1. **Create a new PostgreSQL database**

```powershell
# Connect to PostgreSQL as superuser
psql -U postgres

# Inside psql console:
CREATE DATABASE kooptimizer_db;
CREATE USER kooptimizer_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE kooptimizer_db TO kooptimizer_user;
\q
```

2. **Install required PostgreSQL extensions** (if not already present)

```powershell
psql -U postgres -d kooptimizer_db -c "CREATE EXTENSION IF NOT EXISTS plpython3u;"
psql -U postgres -d kooptimizer_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

3. **Load the schema from db/schema.sql**

```powershell
# Option A: Using psql command line
psql -U postgres -d kooptimizer_db -f db/schema.sql

# Option B: Using full PostgreSQL path (Windows)
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d kooptimizer_db -f db/schema.sql
```

4. **Verify the schema was loaded**

```powershell
# Check tables count (should be 34)
psql -U postgres -d kooptimizer_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Check functions count (should be 39)
psql -U postgres -d kooptimizer_db -c "SELECT COUNT(*) FROM pg_proc WHERE pronamespace = 'public'::regnamespace;"

# List all stored procedures
psql -U postgres -d kooptimizer_db -c "SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace AND prokind = 'p';"
```

5. **Run Django migrations to sync Django's migration history**

```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Create migration records without applying changes (schema already exists)
python manage.py migrate --fake-initial
```

Common tasks
------------

1. **Create migrations (developer)**

```powershell
python manage.py makemigrations
```

2. **Apply migrations (apply to database)**

```powershell
python manage.py migrate
```

3. **Export/Update schema.sql (when DB structure changes)**

```powershell
# Set password as environment variable (Windows)
$env:PGPASSWORD="postgres"

# Export schema-only (no data)
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -s -U postgres -h 127.0.0.1 -p 5432 -d kooptimizer_db2 -f db/schema.sql

# Clear password variable
$env:PGPASSWORD=""
```

4. **Dump database with data (full backup)**

```powershell
# Custom format (recommended - compressed and flexible)
pg_dump -U postgres -h 127.0.0.1 -d kooptimizer_db2 -F c -b -v -f database/backups/kooptimizer_$(Get-Date -Format 'yyyyMMdd').dump

# Plain SQL format (human-readable)
pg_dump -U postgres -h 127.0.0.1 -d kooptimizer_db2 -f database/backups/kooptimizer_$(Get-Date -Format 'yyyyMMdd').sql
```

5. **Restore from backup**

```powershell
# Restore from custom format
pg_restore -U postgres -d kooptimizer_db -v database/backups/kooptimizer_20251206.dump

# Restore from SQL format
psql -U postgres -d kooptimizer_db -f database/backups/kooptimizer_20251206.sql
```


Schema summary (db/schema.sql contents)
---------------------------------------

The `db/schema.sql` file contains a complete PostgreSQL database structure export generated on December 6, 2025 from database `kooptimizer_db2` (PostgreSQL 18).

**Database objects included:**

- **34 Tables**
  - Core: `auth_user`, `auth_group`, `auth_permission`
  - Users: `users_customuser`, `users_userprofile`, `users_staffcooperativeassignment`
  - Cooperatives: `cooperatives_cooperative`, `cooperatives_cooperativeprofile`, `cooperatives_boardmember`, `cooperatives_financialdata`
  - Account Management: `account_management_useraccount`, `account_management_coopaccount`
  - Communications: `communications_announcement`, `communications_message`, `communications_conversation`, `communications_recipient`
  - Dashboard: Various dashboard and databank tables
  - Web Push: `webpush_pushinformation`, `webpush_subscriptioninfo`, `webpush_group`
  - Django framework tables and session management

- **39 Functions** (stored functions and triggers)
  - `get_all_user_accounts()` - Retrieve all user account data with formatting
  - `get_all_profiles_admin()` - Admin view of all cooperative profiles
  - `get_coop_profile_details(p_coop_id)` - Detailed cooperative information
  - `get_profile_by_coop(p_coop_id)` - Profile lookup by cooperative
  - `get_profile_details(p_profile_id)` - Profile details by ID
  - `get_profiles_by_staff(p_staff_id)` - Profiles assigned to staff member
  - `sp_create_user_profile()` - Create new user with profile
  - `sp_complete_first_login()` - Handle first-time login flow
  - `sp_get_account_management_data()` - Account management dashboard data
  - `fn_trigger_set_timestamp()` - Auto-update timestamp trigger function
  - `fn_update_messenger_timestamp()` - Messaging timestamp trigger
  - Plus many more utility and business logic functions

- **10 Stored Procedures**
  - `sp_create_admin_account()` - Create administrator accounts
  - `sp_create_officer_account()` - Create cooperative officer accounts
  - `sp_create_staff_account()` - Create staff accounts with coop assignments
  - `sp_add_coop_profile()` - Add cooperative profile with financial data
  - `sp_update_user_profile()` - Update user profile information
  - `sp_update_account_details()` - Update account details
  - `sp_update_cooperative_profile()` - Update cooperative information
  - `sp_deactivate_user()` - Deactivate user account
  - `sp_reactivate_user()` - Reactivate previously deactivated account
  - `sp_delete_cooperative()` - Remove cooperative and related data

- **7 Custom Types/Enums**
  - `user_role_enum` - User role definitions (admin, staff, officer, etc.)
  - `gender_enum` - Gender options (male, female, other, others)
  - `approval_status_enum` - Approval workflow states (pending, approved)
  - `announcement_status_enum` - Announcement states (sent, draft, scheduled)
  - `announcement_type_enum` - Communication types (sms, e-mail)
  - `verification_status_enum` - Account verification states
  - Plus message and notification related enums

- **37 Indexes** - Performance optimization indexes on:
  - Primary keys and foreign keys
  - Username, email, mobile number lookups
  - Timestamp-based queries
  - Cooperative and profile associations
  - Message and conversation threading

- **Foreign Key Constraints** - Referential integrity for:
  - User-to-profile relationships
  - Cooperative-to-member associations
  - Message threading and conversations
  - Staff-to-cooperative assignments
  - Notification subscriptions

- **Triggers**
  - Auto-update timestamps on row modifications
  - Messenger conversation timestamp updates
  - Data validation triggers

**Database Extensions Required:**
- `plpython3u` - PL/Python3 untrusted procedural language
- `pgcrypto` - Cryptographic functions for password hashing and encryption


**Usage:**
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run a specific script (example)
python scripts/apply_stored_procs.py

# Or apply stored procedures directly from schema.sql (recommended)
psql -U postgres -d kooptimizer_db -f db/schema.sql
```

Troubleshooting
---------------

### Error: "plpython3u extension not available"
Install PL/Python extension:
```powershell
# Install as PostgreSQL superuser
psql -U postgres -d kooptimizer_db -c "CREATE EXTENSION plpython3u;"
```

### Error: "relation already exists"
The schema.sql file creates tables from scratch. Either:
1. Drop existing schema first: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
2. Or use Django migrations instead: `python manage.py migrate`

### Error: "permission denied"
Ensure your PostgreSQL user has sufficient privileges:
```powershell
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE kooptimizer_db TO your_user;"
psql -U postgres -d kooptimizer_db -c "GRANT ALL ON SCHEMA public TO your_user;"
```

### Verifying schema integrity
```powershell
# Check if all stored procedures exist
psql -U postgres -d kooptimizer_db -c "SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace AND prokind = 'p' ORDER BY proname;"

# Check custom types
psql -U postgres -d kooptimizer_db -c "SELECT typname FROM pg_type WHERE typnamespace = 'public'::regnamespace AND typtype = 'e' ORDER BY typname;"

# Verify table count
psql -U postgres -d kooptimizer_db -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
```

Notes and best practices
------------------------
- Do not commit production DB dumps or credential files to the repository.
- Always backup before applying schema changes: `pg_dump -F c -b -v -f backup.dump`
- Use CI to run migrations in controlled environments; prefer a one-way migration path with rollback scripts when possible.
- Keep `db/schema.sql` updated when you make DB-level changes outside Django migrations (e.g., manual indexes or stored procedures).
- Run `python manage.py migrate --fake-initial` after loading schema.sql to sync Django's migration history.
- Test schema changes in development/staging before applying to production.
- Use transactions when applying manual SQL changes: `BEGIN; ... COMMIT;` or `ROLLBACK;` on error.

For production deployments
---------------------------
1. **Always backup first**: Create full dump before any schema changes
2. **Test in staging**: Apply schema.sql to a staging database first
3. **Use migrations**: Prefer Django migrations for incremental changes
4. **Monitor performance**: Check query performance after adding indexes or procedures
5. **Document changes**: Update this file when modifying database structure
6. **Version control**: Commit schema.sql changes with descriptive commit messages

References
----------
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Django Migrations: https://docs.djangoproject.com/en/stable/topics/migrations/
- pg_dump Manual: https://www.postgresql.org/docs/current/app-pgdump.html
- pg_restore Manual: https://www.postgresql.org/docs/current/app-pgrestore.html
