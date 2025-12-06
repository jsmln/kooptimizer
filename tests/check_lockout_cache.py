import os
import sys
import django

# Set environment variable to skip the encoding issue
os.environ['PYTHONIOENCODING'] = 'utf-8'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')

# Suppress print statements that cause encoding issues
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

django.setup()

import time
from datetime import datetime
from django.db import connection
from django.core.cache import cache

print("=" * 70)
print("CHECKING LOCKOUT ACCOUNTS IN CACHE TABLE")
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
            # Get all lockout records (Django adds :1: prefix to cache keys)
            cursor.execute("""
                SELECT cache_key, expires
                FROM cache_table
                WHERE cache_key LIKE '%:login_lockout_%' OR cache_key LIKE 'login_lockout_%'
                ORDER BY expires
            """)
            lockout_records = cursor.fetchall()
            
            # Get all failed attempt records (Django adds :1: prefix to cache keys)
            cursor.execute("""
                SELECT cache_key, expires
                FROM cache_table
                WHERE cache_key LIKE '%:login_attempts_%' OR cache_key LIKE 'login_attempts_%'
                ORDER BY cache_key
            """)
            attempt_records = cursor.fetchall()
            
            print(f"\n[LOCKOUT RECORDS] Found {len(lockout_records)} locked accounts:")
            print("-" * 70)
            
            if lockout_records:
                now = datetime.now()
                for record in lockout_records:
                    cache_key = record[0]
                    expires_datetime = record[1]
                    
                    # Extract username from cache key (remove :1: prefix if present)
                    username = cache_key.replace(':1:login_lockout_', '').replace('login_lockout_', '')
                    
                    # Check if still locked
                    if expires_datetime:
                        # Handle timezone-aware datetime
                        if expires_datetime.tzinfo:
                            from django.utils import timezone
                            now = timezone.now()
                        
                        is_active = expires_datetime > now
                        if is_active:
                            remaining = expires_datetime - now
                            remaining_seconds = int(remaining.total_seconds())
                            remaining_hours = remaining_seconds // 3600
                            remaining_minutes = (remaining_seconds % 3600) // 60
                        else:
                            remaining_hours = 0
                            remaining_minutes = 0
                        
                        status = "ACTIVE" if is_active else "EXPIRED"
                        print(f"Username: {username}")
                        print(f"  Status: {status}")
                        print(f"  Expires: {expires_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                        if is_active:
                            print(f"  Time Remaining: {remaining_hours}h {remaining_minutes}m")
                        print()
            else:
                print("  No lockout records found.")
            
            print(f"\n[FAILED ATTEMPT RECORDS] Found {len(attempt_records)} accounts with failed attempts:")
            print("-" * 70)
            
            if attempt_records:
                for record in attempt_records:
                    cache_key = record[0]
                    expires_timestamp = record[1]
                    
                    # Extract username from cache key (remove :1: prefix if present)
                    username = cache_key.replace(':1:login_attempts_', '').replace('login_attempts_', '')
                    
                    # Get the actual value using Django cache API
                    failed_attempts = cache.get(cache_key)
                    
                    print(f"Username: {username}")
                    if failed_attempts is not None:
                        print(f"  Failed Attempts: {failed_attempts}")
                    else:
                        print(f"  Failed Attempts: (expired or not found)")
                    if expires_timestamp:
                        # expires_timestamp is already a datetime object
                        if isinstance(expires_timestamp, datetime):
                            expires_datetime = expires_timestamp
                        else:
                            expires_datetime = datetime.fromtimestamp(expires_timestamp)
                        print(f"  Expires: {expires_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("  No failed attempt records found.")
            
            # Also check using Django cache API
            print("\n[USING DJANGO CACHE API]")
            print("-" * 70)
            
            # Try to get a sample lockout (if any exist)
            if lockout_records:
                sample_key_db = lockout_records[0][0]
                # Remove Django's cache prefix to get the actual key
                sample_key = sample_key_db.replace(':1:', '')
                sample_username = sample_key.replace('login_lockout_', '')
                cached_value = cache.get(sample_key)
                if cached_value:
                    print(f"Sample check for '{sample_username}':")
                    print(f"  Cache.get() returned: {cached_value}")
                    print(f"  Is locked: {cached_value > int(time.time())}")
                else:
                    print(f"Sample check for '{sample_username}':")
                    print(f"  Cache.get() returned: None (may be expired)")
            
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

