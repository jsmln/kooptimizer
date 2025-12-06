import os
import sys
import django

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

django.setup()

from django.db import connection
from django.core.cache import cache
import time

print("=" * 70)
print("CHECKING CACHE TABLE STRUCTURE")
print("=" * 70)

try:
    with connection.cursor() as cursor:
        # Check if cache_table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'cache_table'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("\n[ERROR] cache_table does not exist!")
            print("Please run: python manage.py createcachetable")
        else:
            print("\n[OK] cache_table exists")
            
            # Get table structure
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'cache_table'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            print("\n[TABLE STRUCTURE]")
            print("-" * 70)
            for col in columns:
                col_name = col[0]
                col_type = col[1]
                col_length = col[2] if col[2] else ""
                print(f"  {col_name:<30} {col_type} {col_length}")
            
            # Get all rows with all columns
            cursor.execute("""
                SELECT *
                FROM cache_table
                ORDER BY cache_key
            """)
            all_records = cursor.fetchall()
            
            print(f"\n[ALL CACHE ENTRIES] Found {len(all_records)} entries:")
            print("-" * 70)
            
            if all_records:
                # Get column names
                col_names = [desc[0] for desc in cursor.description]
                print(f"Columns: {', '.join(col_names)}")
                print()
                
                for record in all_records:
                    print(f"Record:")
                    for i, col_name in enumerate(col_names):
                        value = record[i]
                        if col_name == 'value' and value:
                            # Try to show a preview of the value
                            if isinstance(value, bytes):
                                preview = value[:50] if len(value) > 50 else value
                                print(f"  {col_name}: {preview} (bytes, length: {len(value)})")
                            else:
                                print(f"  {col_name}: {value}")
                        elif col_name == 'expires' and value:
                            from datetime import datetime
                            try:
                                dt = datetime.fromtimestamp(value)
                                print(f"  {col_name}: {value} ({dt.strftime('%Y-%m-%d %H:%M:%S')})")
                            except:
                                print(f"  {col_name}: {value}")
                        else:
                            print(f"  {col_name}: {value}")
                    print()
            else:
                print("  No entries found")
            
            # Test write and immediate read from database
            print("\n[TEST] Writing test value and checking database:")
            test_key = "login_lockout_testuser2"
            test_value = int(time.time()) + 3600
            
            cache.set(test_key, test_value, 3600)
            print(f"  Written to cache: {test_key} = {test_value}")
            
            # Check database immediately
            cursor.execute("""
                SELECT *
                FROM cache_table
                WHERE cache_key = %s
            """, [test_key])
            db_record = cursor.fetchone()
            
            if db_record:
                print(f"  [SUCCESS] Found in database!")
                for i, col_name in enumerate(col_names):
                    print(f"    {col_name}: {db_record[i]}")
            else:
                print(f"  [ERROR] Not found in database!")
                print(f"  But cache.get() returns: {cache.get(test_key)}")
            
            # Clean up
            cache.delete(test_key)
            
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

