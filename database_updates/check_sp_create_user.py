import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

print("=" * 60)
print("CHECKING FOR sp_create_user_profile")
print("=" * 60)

# Check if function/procedure exists
cursor.execute("""
    SELECT routine_name, routine_type
    FROM information_schema.routines 
    WHERE routine_name LIKE '%create_user%'
    AND routine_schema = 'public'
""")

results = cursor.fetchall()

if results:
    print("\nFound related functions/procedures:")
    for name, rtype in results:
        print(f"  - {name} ({rtype})")
else:
    print("\n✗ No sp_create_user_profile found in database")

print("\n" + "=" * 60)
print("ALL STORED PROCEDURES IN DATABASE:")
print("=" * 60)

cursor.execute("""
    SELECT routine_name, routine_type
    FROM information_schema.routines 
    WHERE routine_schema = 'public'
    AND routine_name LIKE 'sp_%'
    ORDER BY routine_name
""")

for name, rtype in cursor.fetchall():
    print(f"  {name} ({rtype})")
