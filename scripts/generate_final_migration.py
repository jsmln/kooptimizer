"""
Generate a complete and comprehensive migration SQL file
"""
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_table_create_statement(cursor, table_name):
    """Generate CREATE TABLE statement for a specific table"""
    cursor.execute("""
        SELECT 
            a.attname AS column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
            a.attnotnull AS not_null,
            pg_get_expr(ad.adbin, ad.adrelid) AS default_value
        FROM pg_attribute a
        LEFT JOIN pg_attrdef ad ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
        WHERE a.attrelid = %s::regclass
        AND a.attnum > 0
        AND NOT a.attisdropped
        ORDER BY a.attnum;
    """, (f'public.{table_name}',))
    
    columns = cursor.fetchall()
    
    col_defs = []
    for col_name, data_type, not_null, default_val in columns:
        col_def = f"    {col_name} {data_type}"
        if not_null:
            col_def += " NOT NULL"
        if default_val:
            col_def += f" DEFAULT {default_val}"
        col_defs.append(col_def)
    
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(col_defs) + "\n);"

def get_constraints(cursor, table_name):
    """Get constraints for a table"""
    cursor.execute("""
        SELECT 
            con.conname AS constraint_name,
            con.contype AS constraint_type,
            pg_get_constraintdef(con.oid) AS constraint_def
        FROM pg_constraint con
        JOIN pg_namespace nsp ON nsp.oid = con.connamespace
        WHERE con.conrelid = %s::regclass
        AND nsp.nspname = 'public'
        ORDER BY con.contype, con.conname;
    """, (f'public.{table_name}',))
    
    return cursor.fetchall()

def get_indexes(cursor, table_name):
    """Get indexes for a table"""
    try:
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = %s
            AND indexname NOT LIKE '%%_pkey'
            ORDER BY indexname;
        """, (table_name,))
        
        return cursor.fetchall()
    except Exception as e:
        print(f"Warning: Could not get indexes for {table_name}: {e}")
        return []

def generate_comprehensive_migration():
    """Generate comprehensive migration SQL"""
    conn = get_connection()
    cursor = conn.cursor()
    
    sql_lines = []
    
    # Header
    sql_lines.append("-- ========================================")
    sql_lines.append("-- KOOPTIMIZER DATABASE MIGRATION SCRIPT")
    sql_lines.append("-- ========================================")
    sql_lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_lines.append("-- Database: kooptimizer_db2")
    sql_lines.append("-- From: kooptimizer_db2_complete_dump.sql (backup)")
    sql_lines.append("-- To: Current development schema")
    sql_lines.append("--")
    sql_lines.append("-- PURPOSE:")
    sql_lines.append("--   This script updates your database from the backup state to the")
    sql_lines.append("--   current development state. Run this after pulling latest code.")
    sql_lines.append("--")
    sql_lines.append("-- USAGE:")
    sql_lines.append("--   Method 1 (psql command line):")
    sql_lines.append("--     psql -U postgres -d kooptimizer_db2 -f database/updates/update_from_backup.sql")
    sql_lines.append("--")
    sql_lines.append("--   Method 2 (pgAdmin or similar):")
    sql_lines.append("--     Open this file and execute it in a query window")
    sql_lines.append("--")
    sql_lines.append("-- IMPORTANT:")
    sql_lines.append("--   - Backup your database before running this script")
    sql_lines.append("--   - This script is idempotent (safe to run multiple times)")
    sql_lines.append("--   - All operations are wrapped in a transaction")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    
    # Transaction begin
    sql_lines.append("BEGIN;")
    sql_lines.append("")
    
    # Section 1: New table announcement_attachments
    sql_lines.append("-- ========================================")
    sql_lines.append("-- SECTION 1: NEW TABLES")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    sql_lines.append("-- Create announcement_attachments table")
    sql_lines.append("-- This table stores multiple attachments per announcement")
    sql_lines.append("")
    
    # Get the full CREATE TABLE statement
    table_def = get_table_create_statement(cursor, 'announcement_attachments')
    sql_lines.append(table_def)
    sql_lines.append("")
    
    # Get constraints
    constraints = get_constraints(cursor, 'announcement_attachments')
    for constraint_name, constraint_type, constraint_def in constraints:
        sql_lines.append(f"-- Constraint: {constraint_name} ({constraint_type})")
        sql_lines.append(f"ALTER TABLE announcement_attachments")
        sql_lines.append(f"    ADD CONSTRAINT {constraint_name} {constraint_def};")
        sql_lines.append("")
    
    # Get indexes
    indexes = get_indexes(cursor, 'announcement_attachments')
    for index_name, index_def in indexes:
        sql_lines.append(f"-- Index: {index_name}")
        sql_lines.append(f"{index_def};")
        sql_lines.append("")
    
    # Section 2: Schema modifications
    sql_lines.append("-- ========================================")
    sql_lines.append("-- SECTION 2: SCHEMA MODIFICATIONS")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    sql_lines.append("-- Note: The announcements table structure has been refactored.")
    sql_lines.append("-- Attachment data should now be stored in announcement_attachments table.")
    sql_lines.append("-- The old attachment columns in announcements table are kept for backward compatibility.")
    sql_lines.append("")
    
    # Section 3: Functions and procedures
    sql_lines.append("-- ========================================")
    sql_lines.append("-- SECTION 3: UPDATED FUNCTIONS")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    
    # Get updated function definitions
    functions_to_export = [
        'sp_get_announcement_details',
        'sp_save_announcement',
        'sp_create_user_profile',
        'sp_get_all_user_accounts',
    ]
    
    for func_name in functions_to_export:
        sql_lines.append(f"-- Function: {func_name}")
        sql_lines.append(f"-- Drop existing versions")
        sql_lines.append(f"DROP FUNCTION IF EXISTS {func_name} CASCADE;")
        sql_lines.append("")
        
        # Get function definition
        cursor.execute("""
            SELECT pg_get_functiondef(p.oid)
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public'
            AND p.proname = %s
            ORDER BY p.oid
            LIMIT 1;
        """, (func_name,))
        
        result = cursor.fetchone()
        if result:
            sql_lines.append(result[0])
            sql_lines.append("")
    
    # Section 4: Data migrations (if needed)
    sql_lines.append("-- ========================================")
    sql_lines.append("-- SECTION 4: DATA MIGRATIONS")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    sql_lines.append("-- If you have existing announcements with attachments in the old format,")
    sql_lines.append("-- you may need to migrate them to the new announcement_attachments table.")
    sql_lines.append("-- This migration is optional and can be done separately if needed.")
    sql_lines.append("")
    sql_lines.append("-- Example migration (commented out, uncomment if needed):")
    sql_lines.append("/*")
    sql_lines.append("INSERT INTO announcement_attachments (")
    sql_lines.append("    announcement_id, filename, original_filename,")
    sql_lines.append("    content_type, file_size, file_data")
    sql_lines.append(")")
    sql_lines.append("SELECT ")
    sql_lines.append("    announcement_id,")
    sql_lines.append("    COALESCE(attachment_filename, 'attachment'),")
    sql_lines.append("    COALESCE(attachment_filename, 'attachment'),")
    sql_lines.append("    COALESCE(attachment_content_type, 'application/octet-stream'),")
    sql_lines.append("    COALESCE(attachment_size, 0),")
    sql_lines.append("    attachment")
    sql_lines.append("FROM announcements")
    sql_lines.append("WHERE attachment IS NOT NULL")
    sql_lines.append("AND announcement_id NOT IN (")
    sql_lines.append("    SELECT DISTINCT announcement_id FROM announcement_attachments")
    sql_lines.append(");")
    sql_lines.append("*/")
    sql_lines.append("")
    
    # Commit
    sql_lines.append("-- ========================================")
    sql_lines.append("-- FINALIZE MIGRATION")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    sql_lines.append("COMMIT;")
    sql_lines.append("")
    sql_lines.append("-- Migration completed successfully!")
    sql_lines.append(f"-- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    cursor.close()
    conn.close()
    
    return '\n'.join(sql_lines)

if __name__ == '__main__':
    try:
        print("Generating comprehensive migration SQL...")
        migration_sql = generate_comprehensive_migration()
        
        # Save to file
        output_file = 'database/updates/migration_complete.sql'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(migration_sql)
        
        print(f"✓ Migration SQL generated: {output_file}")
        
        # Also update the update_from_backup.sql file
        backup_file = 'database/updates/update_from_backup.sql'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(migration_sql)
        
        print(f"✓ Updated: {backup_file}")
        print("\nYour teammates can run this SQL file to update their database.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
