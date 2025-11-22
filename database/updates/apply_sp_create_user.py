import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

# Read the SQL file
with open('stored_procedures/sp_create_user_profile.sql', 'r') as f:
    sql = f.read()

print("=" * 60)
print("APPLYING sp_create_user_profile")
print("=" * 60)

try:
    with connection.cursor() as cursor:
        cursor.execute(sql)
    print("\n✓ Successfully created/updated sp_create_user_profile")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
