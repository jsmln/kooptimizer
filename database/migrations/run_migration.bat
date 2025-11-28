@echo off
REM Run this script to execute the profile_data migration
REM Make sure PostgreSQL is installed and psql is in your PATH

echo Executing profile_data migration...
echo.

REM Replace these values with your database credentials
set PGHOST=127.0.0.1
set PGPORT=5432
set PGDATABASE=kooptimizer_db2
set PGUSER=postgres
REM Set PGPASSWORD if needed, or it will prompt

psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f "database\migrations\add_report_year_to_profile_data.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Migration completed successfully!
) else (
    echo.
    echo Migration failed! Check the error messages above.
    pause
)

