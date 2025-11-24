# Database Updates & Migrations

This folder contains all database migration scripts, test files, update utilities, and diagnostic tools for the Kooptimizer system.

## 🚀 IMPORTANT: For Teammates Pulling Latest Code

**Last Updated:** November 22, 2025

### Quick Migration Steps

After pulling the latest code from GitHub, update your database with this command:

```powershell
# Method 1: Using psql
psql -U postgres -d kooptimizer_db2 -f database/updates/update_from_backup.sql

# Method 2: Using pgAdmin
# Open database/updates/update_from_backup.sql in pgAdmin Query Tool and execute
```

**What this does:**
- ✅ Creates new `announcement_attachments` table for multiple file uploads
- ✅ Updates stored procedures (`sp_get_announcement_details`, `sp_save_announcement`, etc.)
- ✅ Maintains backward compatibility with existing data
- ✅ Safe to run multiple times (idempotent)

**Before migration:**
```powershell
# Backup your database first!
pg_dump -U postgres -d kooptimizer_db2 > my_backup.sql
```

See detailed migration guide at the end of this file.

---

## Contents

### Migration Scripts
- `001_update_cooperatives_schema.sql` - Adds category and district columns, removes mobile_number
- `apply_all_db_changes.sql` - Master script to apply all database changes

### Update Scripts
- `update_sp_get_announcement_details.sql` - Updates announcement details stored procedure
- `update_sp_get_announcements_by_status.sql` - Updates announcements by status procedure

### Test Scripts
- `test_ocr_service.py` - Test OCR service integration
- `test_attachment_debug.py` - Debug attachment functionality
- `test_announcement_details.py` - Test announcement details retrieval
- `test_announcement_features.py` - Test announcement features
- `test_contacts_view.py` - Test contacts view
- `test_conversation_view.py` - Test conversation view
- `test_draft_load.py` - Test draft loading
- `test_email_announcement.py` - Test email announcement sending
- `test_register_user_sp.py` - Test user registration stored procedure
- `test_scheduled.py` - Test scheduled announcements
- `test_sp_bytea.py` - Test bytea data handling
- `test_view_upload.py` - Test view upload functionality

### Check/Diagnostic Scripts
- `check_all_tables.py` - Verify all database tables
- `check_enums.py` - Check enum types in database
- `check_messages_db.py` - Verify messages database structure
- `check_model_db_sync.py` - Check Django models sync with database
- `check_sp_create_user.py` - Verify user creation stored procedure

### Utility Scripts
- `fix_email_enum.py` - Fix email enum issues
- `get_sp_definition.py` - Retrieve stored procedure definitions

### Stored Procedures
See `../stored_procedures/` for:
- `sp_add_cooperative.sql`
- `sp_display_cooperatives.sql`
- `sp_edit_cooperative.sql`
- `sp_delete_cooperative.sql`
- `USAGE_EXAMPLES.sql`

## Usage

### Apply Database Updates
```bash
psql -U your_user -d kooptimizer

\i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/database_updates/apply_all_db_changes.sql
```

### Run Tests
```bash
cd database_updates
python test_ocr_service.py
python test_announcement_features.py
# ... etc
```

### Check Database Health
```bash
python check_all_tables.py
python check_model_db_sync.py
python check_enums.py
```

### Fix Issues
```bash
python fix_email_enum.py
```

## Documentation
See `../OCR_IMPLEMENTATION_README.md` and `../IMPLEMENTATION_SUMMARY.md` for complete documentation.

