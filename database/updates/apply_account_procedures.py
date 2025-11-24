import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

stored_procedures = [
    ('stored_procedures/sp_create_user_profile.sql', 'sp_create_user_profile'),
    ('stored_procedures/sp_update_user_profile.sql', 'sp_update_user_profile'),
]

print("=" * 80)
print("APPLYING STORED PROCEDURES FOR ACCOUNT MANAGEMENT")
print("=" * 80)

for filepath, name in stored_procedures:
    print(f"\n{name}:")
    print("-" * 60)
    
    try:
        with open(filepath, 'r') as f:
            sql = f.read()
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
        
        print(f"✓ Successfully applied {name}")
        
    except FileNotFoundError:
        print(f"✗ File not found: {filepath}")
    except Exception as e:
        print(f"✗ Error applying {name}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
