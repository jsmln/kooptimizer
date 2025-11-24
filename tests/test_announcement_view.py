import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

# Test the stored procedure with an announcement that has attachment
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM sp_get_announcement_details(%s);", [35])
        row = cursor.fetchone()
        
        if row:
            print("SUCCESS! Row data:")
            print(f"Number of columns: {len(row)}")
            for i, value in enumerate(row):
                print(f"Column {i}: {type(value).__name__} = {value}")
        else:
            print("No announcement found with ID 35")
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
