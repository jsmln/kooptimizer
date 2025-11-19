import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

print("=" * 80)
print("sp_create_user_profile DEFINITION")
print("=" * 80)

cursor.execute("""
    SELECT 
        p.proname as function_name,
        pg_get_function_arguments(p.oid) as arguments,
        pg_get_functiondef(p.oid) as definition
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.proname = 'sp_create_user_profile'
""")

result = cursor.fetchone()

if result:
    func_name, arguments, definition = result
    print(f"\nFunction: {func_name}")
    print(f"\nArguments:\n{arguments}")
    print(f"\nFull Definition:\n{definition}")
else:
    print("\n✗ Function not found")
