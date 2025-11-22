"""
Check announcement enum values
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check announcement_type_enum values
    cursor.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
        WHERE pg_type.typname = 'announcement_type_enum'
        ORDER BY enumsortorder;
    """)
    type_values = [row[0] for row in cursor.fetchall()]
    print(f"announcement_type_enum values: {type_values}")
    
    # Check announcement_status_enum values
    cursor.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
        WHERE pg_type.typname = 'announcement_status_enum'
        ORDER BY enumsortorder;
    """)
    status_values = [row[0] for row in cursor.fetchall()]
    print(f"announcement_status_enum values: {status_values}")
