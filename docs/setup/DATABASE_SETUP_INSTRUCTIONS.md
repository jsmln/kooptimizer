# Kooptimizer Database Setup Instructions

## Overview
This document provides instructions for setting up the `kooptimizer_db2` database with the complete schema and data.

**Database Dump File:** `kooptimizer_db2_complete_dump.sql`  
**File Size:** ~34.79 MB  
**Created:** November 21, 2025

## Prerequisites
- PostgreSQL installed (tested with PostgreSQL 18)
- User account with database creation privileges (typically `postgres`)

## Setup Instructions

### Option 1: Create New Database and Restore (Recommended)

1. **Open PowerShell or Command Prompt**

2. **Create a new database** (if not already created):
   ```powershell
   # Set password environment variable (replace 'postgres' with your password)
   $env:PGPASSWORD="postgres"
   
   # Create the database
   & "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h 127.0.0.1 -p 5432 -U postgres kooptimizer_db2
   ```

3. **Restore the database dump**:
   ```powershell
   # Set password environment variable
   $env:PGPASSWORD="postgres"
   
   # Restore the dump (this may take a few minutes)
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d kooptimizer_db2 -f "kooptimizer_db2_complete_dump.sql"
   ```

### Option 2: Drop and Recreate (Clean Install)

If you already have a `kooptimizer_db2` database and want to start fresh:

```powershell
# Set password
$env:PGPASSWORD="postgres"

# Drop existing database (WARNING: This deletes all data!)
& "C:\Program Files\PostgreSQL\18\bin\dropdb.exe" -h 127.0.0.1 -p 5432 -U postgres kooptimizer_db2

# Create new database
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h 127.0.0.1 -p 5432 -U postgres kooptimizer_db2

# Restore the dump
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d kooptimizer_db2 -f "kooptimizer_db2_complete_dump.sql"
```

### Option 3: Using pgAdmin (GUI Method)

1. Open pgAdmin
2. Right-click on "Databases" and select "Create" → "Database"
3. Enter `kooptimizer_db2` as the database name and click "Save"
4. Right-click on the newly created database and select "Restore"
5. Select the file `kooptimizer_db2_complete_dump.sql`
6. Click "Restore"

## Django Configuration

After restoring the database, update your Django `settings.py` file:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kooptimizer_db2',
        'USER': 'postgres',  # Your PostgreSQL username
        'PASSWORD': 'postgres',  # Your PostgreSQL password
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

## Verification

To verify the database was restored correctly:

```powershell
# Set password
$env:PGPASSWORD="postgres"

# List all tables
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d kooptimizer_db2 -c "\dt"

# Check table counts
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d kooptimizer_db2 -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';"
```

Or run Django migrations check:
```bash
python manage.py migrate --check
```

## What's Included

This dump file includes:
- ✅ Complete database schema (all tables, indexes, constraints)
- ✅ All stored procedures and functions
- ✅ All enum types
- ✅ All data from every table (using INSERT statements)
- ✅ Sequences and their current values
- ✅ Triggers and rules
- ✅ Comments and metadata

## Troubleshooting

### Error: "database already exists"
- Use Option 2 above to drop and recreate, or restore into a differently named database

### Error: "permission denied"
- Make sure you're using a PostgreSQL user with sufficient privileges
- Try using the `postgres` superuser account

### Error: "relation already exists"
- The database may already have some tables. Use a fresh database or drop existing one first

### Slow restore process
- This is normal for large databases. The restore may take 5-10 minutes depending on your system

### Path issues with PostgreSQL commands
- Adjust the PostgreSQL path if your installation is in a different location
- Find your installation: `Get-ChildItem "C:\Program Files\PostgreSQL" -Directory`

## Notes for Team Members

- Make sure you're all using the same database name: `kooptimizer_db2`
- Keep your database credentials consistent across the team (or use environment variables)
- This dump was created using `--column-inserts` flag for better readability and debugging
- If you encounter any issues, check that your PostgreSQL version is compatible (18+ recommended)

## Security Note

⚠️ **Important:** This dump file may contain sensitive data including:
- User passwords (hashed)
- API keys
- Personal information
- Business data

**Do NOT:**
- Share this file publicly
- Commit it to public repositories
- Send it through unsecured channels

**Do:**
- Share only with authorized team members
- Use secure file transfer methods
- Consider using `.gitignore` to prevent accidental commits

## Additional Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Django Database Documentation: https://docs.djangoproject.com/en/stable/ref/databases/
- pg_dump documentation: https://www.postgresql.org/docs/current/app-pgdump.html
