"""
Script to compare current database schema with backup and generate migration SQL
"""
import psycopg2
import json
from datetime import datetime

DB_CONFIG = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

def get_connection():
    """Establish database connection"""
    return psycopg2.connect(**DB_CONFIG)

def get_all_tables(cursor):
    """Get all tables in the public schema"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_structure(cursor, table_name):
    """Get detailed table structure"""
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
    return cursor.fetchall()

def get_all_enums(cursor):
    """Get all ENUM types"""
    cursor.execute("""
        SELECT 
            t.typname as enum_name,
            e.enumlabel as enum_value,
            e.enumsortorder
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'public'
        ORDER BY t.typname, e.enumsortorder;
    """)
    results = cursor.fetchall()
    
    enums = {}
    for enum_name, enum_value, sort_order in results:
        if enum_name not in enums:
            enums[enum_name] = []
        enums[enum_name].append(enum_value)
    
    return enums

def get_all_functions(cursor):
    """Get all functions and stored procedures"""
    cursor.execute("""
        SELECT 
            routine_name,
            routine_type,
            data_type
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_type IN ('FUNCTION', 'PROCEDURE')
        ORDER BY routine_name;
    """)
    return cursor.fetchall()

def get_function_definition(cursor, function_name):
    """Get function definition"""
    cursor.execute("""
        SELECT pg_get_functiondef(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        AND p.proname = %s
        LIMIT 1;
    """, (function_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_constraints(cursor, table_name):
    """Get table constraints"""
    cursor.execute("""
        SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        LEFT JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.table_schema = 'public'
        AND tc.table_name = %s
        ORDER BY tc.constraint_type, tc.constraint_name;
    """, (table_name,))
    return cursor.fetchall()

def get_indexes(cursor, table_name):
    """Get table indexes"""
    cursor.execute("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s
        ORDER BY indexname;
    """, (table_name,))
    return cursor.fetchall()

def analyze_database():
    """Analyze current database structure"""
    print("Connecting to database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'tables': {},
        'enums': {},
        'functions': [],
        'procedures': []
    }
    
    print("Fetching ENUMs...")
    analysis['enums'] = get_all_enums(cursor)
    
    print("Fetching tables...")
    tables = get_all_tables(cursor)
    
    for table in tables:
        print(f"  Analyzing table: {table}")
        analysis['tables'][table] = {
            'columns': get_table_structure(cursor, table),
            'constraints': get_constraints(cursor, table),
            'indexes': get_indexes(cursor, table)
        }
    
    print("Fetching functions and procedures...")
    routines = get_all_functions(cursor)
    for routine_name, routine_type, data_type in routines:
        if routine_type == 'FUNCTION':
            analysis['functions'].append(routine_name)
        else:
            analysis['procedures'].append(routine_name)
    
    cursor.close()
    conn.close()
    
    return analysis

def export_current_schema():
    """Export current database schema to SQL file"""
    print("\nExporting current database schema...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    output_lines = []
    output_lines.append("-- Current Database Schema Export")
    output_lines.append(f"-- Generated: {datetime.now().isoformat()}")
    output_lines.append("-- Database: kooptimizer_db2")
    output_lines.append("\n")
    
    # Export ENUMs
    output_lines.append("-- ========================================")
    output_lines.append("-- ENUM TYPES")
    output_lines.append("-- ========================================\n")
    
    enums = get_all_enums(cursor)
    for enum_name, values in enums.items():
        output_lines.append(f"-- ENUM: {enum_name}")
        output_lines.append(f"-- Values: {', '.join(values)}\n")
    
    # Export tables
    output_lines.append("-- ========================================")
    output_lines.append("-- TABLES")
    output_lines.append("-- ========================================\n")
    
    tables = get_all_tables(cursor)
    for table in tables:
        output_lines.append(f"-- TABLE: {table}")
        columns = get_table_structure(cursor, table)
        for col in columns:
            col_name, data_type, max_len, default, nullable, udt_name = col
            output_lines.append(f"--   {col_name}: {data_type}" + 
                              (f"({max_len})" if max_len else "") +
                              (" NOT NULL" if nullable == 'NO' else ""))
        output_lines.append("")
    
    # Export functions
    output_lines.append("-- ========================================")
    output_lines.append("-- FUNCTIONS AND PROCEDURES")
    output_lines.append("-- ========================================\n")
    
    routines = get_all_functions(cursor)
    for routine_name, routine_type, _ in routines:
        output_lines.append(f"-- {routine_type}: {routine_name}")
    
    cursor.close()
    conn.close()
    
    schema_file = 'database/backups/current_schema_analysis.txt'
    with open(schema_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Schema analysis saved to: {schema_file}")
    
    return '\n'.join(output_lines)

if __name__ == '__main__':
    try:
        analysis = analyze_database()
        
        print("\n" + "="*60)
        print("DATABASE ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Tables: {len(analysis['tables'])}")
        print(f"Total ENUMs: {len(analysis['enums'])}")
        print(f"Total Functions: {len(analysis['functions'])}")
        print(f"Total Procedures: {len(analysis['procedures'])}")
        print("="*60)
        
        print("\nTables:")
        for table in sorted(analysis['tables'].keys()):
            print(f"  - {table}")
        
        print("\nENUM Types:")
        for enum_name, values in sorted(analysis['enums'].items()):
            print(f"  - {enum_name}: {values}")
        
        print("\nFunctions:")
        for func in sorted(analysis['functions']):
            print(f"  - {func}")
        
        print("\nProcedures:")
        for proc in sorted(analysis['procedures']):
            print(f"  - {proc}")
        
        # Export schema
        export_current_schema()
        
        # Save analysis as JSON
        analysis_file = 'database/backups/current_db_analysis.json'
        with open(analysis_file, 'w', encoding='utf-8') as f:
            # Convert to serializable format
            serializable_analysis = {
                'timestamp': analysis['timestamp'],
                'tables': {k: {'column_count': len(v['columns'])} for k, v in analysis['tables'].items()},
                'enums': analysis['enums'],
                'functions': analysis['functions'],
                'procedures': analysis['procedures']
            }
            json.dump(serializable_analysis, f, indent=2)
        
        print(f"\nAnalysis saved to: {analysis_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
