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
print("TESTING CACHE WRITE FUNCTIONALITY")
print("=" * 70)

try:
    # Check if cache_table exists
    with connection.cursor() as cursor:
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
            
            # Test writing to cache
            test_key = "login_lockout_testuser"
            test_value = int(time.time()) + 3600  # 1 hour from now
            
            print(f"\n[TEST] Writing to cache:")
            print(f"  Key: {test_key}")
            print(f"  Value: {test_value}")
            
            # Write to cache
            result = cache.set(test_key, test_value, 3600)
            print(f"  cache.set() returned: {result}")
            
            # Verify it was written
            with connection.cursor() as cursor2:
                cursor2.execute("""
                    SELECT cache_key, value, expires
                    FROM cache_table
                    WHERE cache_key = %s
                """, [test_key])
                row = cursor2.fetchone()
                
                if row:
                    print(f"\n[SUCCESS] Found in database:")
                    print(f"  Key: {row[0]}")
                    print(f"  Expires: {row[2]}")
                else:
                    print(f"\n[ERROR] Not found in database after cache.set()")
            
            # Test reading back
            read_value = cache.get(test_key)
            print(f"\n[TEST] Reading from cache:")
            print(f"  cache.get() returned: {read_value}")
            
            if read_value == test_value:
                print("  [SUCCESS] Value matches!")
            else:
                print(f"  [ERROR] Value mismatch! Expected {test_value}, got {read_value}")
            
            # Clean up test key
            cache.delete(test_key)
            print(f"\n[TEST] Cleaned up test key")
            
            # Now check for actual lockout records
            print(f"\n[CHECK] Looking for actual lockout records:")
            with connection.cursor() as cursor3:
                cursor3.execute("""
                    SELECT cache_key, expires
                    FROM cache_table
                    WHERE cache_key LIKE 'login_lockout_%'
                    ORDER BY expires
                """)
                lockout_records = cursor3.fetchall()
                
                if lockout_records:
                    print(f"  Found {len(lockout_records)} lockout records:")
                    for record in lockout_records:
                        print(f"    - {record[0]} (expires: {record[2]})")
                else:
                    print("  No lockout records found")
                    
            # Check for failed attempt records
            print(f"\n[CHECK] Looking for failed attempt records:")
            with connection.cursor() as cursor4:
                cursor4.execute("""
                    SELECT cache_key, expires
                    FROM cache_table
                    WHERE cache_key LIKE 'login_attempts_%'
                    ORDER BY cache_key
                """)
                attempt_records = cursor4.fetchall()
                
                if attempt_records:
                    print(f"  Found {len(attempt_records)} attempt records:")
                    for record in attempt_records:
                        print(f"    - {record[0]} (expires: {record[2]})")
                else:
                    print("  No attempt records found")
                    
            # List ALL cache entries to see what's there
            print(f"\n[CHECK] All cache entries:")
            with connection.cursor() as cursor5:
                cursor5.execute("""
                    SELECT cache_key, expires
                    FROM cache_table
                    ORDER BY cache_key
                """)
                all_records = cursor5.fetchall()
                
                if all_records:
                    print(f"  Found {len(all_records)} total cache entries:")
                    for record in all_records[:20]:  # Show first 20
                        print(f"    - {record[0]} (expires: {record[2]})")
                    if len(all_records) > 20:
                        print(f"    ... and {len(all_records) - 20} more")
                else:
                    print("  No cache entries found")
            
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

