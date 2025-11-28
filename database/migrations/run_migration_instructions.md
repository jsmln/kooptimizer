# How to Run the Profile Data Migration

## Option 1: Using psql (PostgreSQL Command Line)

### Windows (PowerShell or Command Prompt):
```bash
# Navigate to project root
cd C:\Users\Noe Gonzales\Downloads\System\Kooptimizer

# Run using psql (replace with your database credentials)
psql -h 127.0.0.1 -p 5432 -U postgres -d kooptimizer_db2 -f "database\migrations\add_report_year_to_profile_data.sql"
```

### Or use the batch file:
```bash
# Double-click or run:
database\migrations\run_migration.bat
```

## Option 2: Using pgAdmin

1. Open pgAdmin
2. Connect to your database server
3. Right-click on `kooptimizer_db2` database
4. Select "Query Tool"
5. Open the file: `database/migrations/add_report_year_to_profile_data.sql`
6. Click "Execute" (F5)

## Option 3: Using Django Database Shell

```bash
# In your project directory
python manage.py dbshell

# Then copy and paste the SQL commands from:
# database/migrations/add_report_year_to_profile_data.sql
```

## Option 4: Using Python Script

Run this Python script:

```python
import psycopg2
import os

# Database connection parameters
conn_params = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'your_password'  # Replace with your password
}

# Read SQL file
sql_file_path = os.path.join('database', 'migrations', 'add_report_year_to_profile_data.sql')
with open(sql_file_path, 'r') as f:
    sql = f.read()

# Execute
conn = psycopg2.connect(**conn_params)
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print("Migration completed successfully!")
```

## Verification

After running the migration, verify it worked:

```sql
-- Check if report_year column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'profile_data' AND column_name = 'report_year';

-- Check if unique constraint was removed
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'profile_data' AND indexname = 'profile_data_coop_id_key';
-- Should return no rows (constraint removed)

-- Check new unique constraint
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'profile_data' AND indexname = 'profile_data_coop_year_unique';
-- Should return one row (new constraint exists)

-- Check existing data
SELECT coop_id, report_year, COUNT(*) 
FROM profile_data 
GROUP BY coop_id, report_year;
```

