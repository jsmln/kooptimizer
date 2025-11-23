import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

# List of tables to check
tables_to_check = [
    'users',
    'admin',
    'staff', 
    'cooperatives',
    'officers',
    'messages',
    'message_recipients',
    'announcements',
    'profile_data',
    'financial_data',
    'members'
]

cursor = connection.cursor()

for table_name in tables_to_check:
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")
    
    try:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        
        rows = cursor.fetchall()
        if rows:
            for col_name, data_type, nullable in rows:
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                print(f"  {col_name:<30} {data_type:<25} {null_str}")
        else:
            print(f"  Table not found or no columns")
            
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n{'='*60}")
print("SCAN COMPLETE")
print(f"{'='*60}")
