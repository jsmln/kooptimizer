import os
from django.contrib.auth.hashers import make_password

# --- Configuration ---
# Set this to your project's settings module path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings') 
# --- End Configuration ---

try:
    # This setup is required to use Django components standalone
    import django
    django.setup()
except ImportError:
    print("Error: Django not found.")
    print("Please run 'pip install django' in your environment.")
    exit()
except Exception as e:
    print(f"Error loading Django settings: {e}")
    print("Make sure you run this script from your project's root directory.")
    print("And that 'kooptimizer.settings' is your correct settings file path.")
    exit()

# The list of passwords you want to convert
passwords_to_hash = [
    'StaffMark@123!',
    'OfficerLuis@123!',
    'AdminJoan@123!',
    'StaffRyan@123!',
    'OfficerKate@123!'
]

print(f"--- Generating Hashes (Using Django's default: pbkdf2_sha256) ---")
print("NOTE: These hashes will be DIFFERENT every time you run this script.\n")

for plain_password in passwords_to_hash:
    
    # This is the "manual" conversion function
    new_hash = make_password(plain_password)
    
    print(f"Password: {plain_password}")
    print(f"Hash:     {new_hash}\n")
