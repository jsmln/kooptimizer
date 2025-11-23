"""
Generate migration SQL by comparing backup dump with current database
"""
import psycopg2
import re
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

def get_current_tables(cursor):
    """Get all current tables"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    return {row[0] for row in cursor.fetchall()}

def get_current_columns(cursor, table_name):
    """Get columns for a table"""
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            column_default,
            is_nullable,
            udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    return {row[0]: row for row in cursor.fetchall()}

def get_current_functions(cursor):
    """Get all current functions"""
    cursor.execute("""
        SELECT DISTINCT
            routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_type = 'FUNCTION'
        ORDER BY routine_name;
    """)
    return {row[0] for row in cursor.fetchall()}

def get_function_signatures(cursor, function_name):
    """Get all overloaded signatures for a function"""
    cursor.execute("""
        SELECT 
            pg_get_functiondef(p.oid) as definition,
            pg_get_function_arguments(p.oid) as arguments
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        AND p.proname = %s;
    """, (function_name,))
    return cursor.fetchall()

def generate_migration_sql():
    """Generate migration SQL file"""
    print("Connecting to database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    migration_sql = []
    migration_sql.append("-- ========================================")
    migration_sql.append("-- Database Migration Script")
    migration_sql.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    migration_sql.append("-- Database: kooptimizer_db2")
    migration_sql.append("-- Purpose: Update database schema to match latest codebase")
    migration_sql.append("-- ========================================")
    migration_sql.append("")
    migration_sql.append("-- This script updates the database schema from the backup state")
    migration_sql.append("-- to the current development state.")
    migration_sql.append("")
    migration_sql.append("BEGIN;")
    migration_sql.append("")
    
    # Check for new tables
    print("Checking for schema changes...")
    current_tables = get_current_tables(cursor)
    
    # Known backup tables from the dump file
    backup_tables = {
        'admin', 'announcement_officer_recipients', 'announcement_recipients',
        'announcements', 'auth_group', 'auth_group_permissions', 'auth_permission',
        'auth_user', 'auth_user_groups', 'auth_user_user_permissions',
        'cooperatives', 'django_admin_log', 'django_content_type',
        'django_migrations', 'django_session', 'financial_data', 'members',
        'message_recipients', 'messages', 'messenger_conversations',
        'messenger_messages', 'messenger_participants', 'officers',
        'profile_data', 'staff', 'users'
    }
    
    new_tables = current_tables - backup_tables
    
    if new_tables:
        migration_sql.append("-- ========================================")
        migration_sql.append("-- NEW TABLES")
        migration_sql.append("-- ========================================")
        migration_sql.append("")
        
        for table in sorted(new_tables):
            print(f"  Found new table: {table}")
            
            # Get CREATE TABLE statement
            cursor.execute("""
                SELECT 
                    'CREATE TABLE ' || table_name || ' (' || 
                    string_agg(
                        column_name || ' ' || 
                        CASE 
                            WHEN data_type = 'USER-DEFINED' THEN udt_name
                            WHEN character_maximum_length IS NOT NULL 
                            THEN data_type || '(' || character_maximum_length || ')'
                            ELSE data_type 
                        END ||
                        CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                        CASE WHEN column_default IS NOT NULL 
                            THEN ' DEFAULT ' || column_default 
                            ELSE '' 
                        END,
                        ', '
                        ORDER BY ordinal_position
                    ) || ');' as create_statement
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                GROUP BY table_name;
            """, (table,))
            
            result = cursor.fetchone()
            if result:
                migration_sql.append(f"-- Create table: {table}")
                migration_sql.append(result[0])
                migration_sql.append("")
                
                # Get primary key
                cursor.execute("""
                    SELECT
                        'ALTER TABLE ' || tc.table_name || 
                        ' ADD CONSTRAINT ' || tc.constraint_name || 
                        ' PRIMARY KEY (' || string_agg(kcu.column_name, ', ') || ');'
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    AND tc.constraint_type = 'PRIMARY KEY'
                    GROUP BY tc.table_name, tc.constraint_name;
                """, (table,))
                
                pk_result = cursor.fetchone()
                if pk_result:
                    migration_sql.append(pk_result[0])
                    migration_sql.append("")
    
    # Check for new columns in existing tables
    migration_sql.append("-- ========================================")
    migration_sql.append("-- TABLE MODIFICATIONS")
    migration_sql.append("-- ========================================")
    migration_sql.append("")
    
    # Check announcements table for new columns
    print("Checking for new columns in existing tables...")
    
    # Check if announcement_attachments table exists (this is the key difference)
    if 'announcement_attachments' in new_tables:
        migration_sql.append("-- Note: New separate table for announcement attachments")
        migration_sql.append("-- (Already handled in NEW TABLES section)")
        migration_sql.append("")
    
    # Check announcements table columns
    announcements_cols = get_current_columns(cursor, 'announcements')
    
    # Based on the backup, these attachment columns should be removed if they exist
    attachment_cols_in_announcements = [
        'attachment', 'attachment_filename', 
        'attachment_content_type', 'attachment_size'
    ]
    
    has_attachment_cols = any(col in announcements_cols for col in attachment_cols_in_announcements)
    
    if has_attachment_cols and 'announcement_attachments' in new_tables:
        migration_sql.append("-- Migrate attachment data from announcements to announcement_attachments")
        migration_sql.append("-- (This will be handled by a separate data migration if needed)")
        migration_sql.append("")
    
    # Check for modified functions
    migration_sql.append("-- ========================================")
    migration_sql.append("-- FUNCTIONS AND PROCEDURES")
    migration_sql.append("-- ========================================")
    migration_sql.append("")
    
    print("Exporting current function definitions...")
    
    # Get all functions that need to be created/updated
    current_functions = get_current_functions(cursor)
    
    # Export key functions (limit to avoid huge file)
    key_functions = [
        'sp_create_user_profile',
        'sp_get_all_user_accounts',
        'sp_save_announcement',
        'sp_get_announcement_details',
        'sp_send_message',
        'sp_get_conversation',
        'verify_pbkdf2_sha256'
    ]
    
    for func_name in key_functions:
        if func_name in current_functions:
            print(f"  Exporting function: {func_name}")
            signatures = get_function_signatures(cursor, func_name)
            
            for definition, arguments in signatures:
                if definition:
                    migration_sql.append(f"-- Function: {func_name}({arguments})")
                    migration_sql.append(definition)
                    migration_sql.append("")
    
    # Add any table-specific updates
    migration_sql.append("-- ========================================")
    migration_sql.append("-- DATA UPDATES (if needed)")
    migration_sql.append("-- ========================================")
    migration_sql.append("")
    migration_sql.append("-- Add any necessary data migrations here")
    migration_sql.append("")
    
    # Commit transaction
    migration_sql.append("COMMIT;")
    migration_sql.append("")
    migration_sql.append("-- ========================================")
    migration_sql.append("-- Migration Complete")
    migration_sql.append("-- ========================================")
    
    cursor.close()
    conn.close()
    
    return '\n'.join(migration_sql)

if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("GENERATING MIGRATION SQL")
        print("="*60 + "\n")
        
        migration_sql = generate_migration_sql()
        
        # Save migration file
        output_file = f'database/updates/migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(migration_sql)
        
        print("\n" + "="*60)
        print(f"Migration SQL generated successfully!")
        print(f"File: {output_file}")
        print("="*60)
        
        # Also create a simple update file for teammates
        simple_update = f'database/updates/update_from_backup.sql'
        with open(simple_update, 'w', encoding='utf-8') as f:
            f.write(migration_sql)
        
        print(f"\nAlso saved as: {simple_update}")
        print("\nTeammates can run this SQL file to update their database:")
        print("  psql -U postgres -d kooptimizer_db2 -f database/updates/update_from_backup.sql")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
