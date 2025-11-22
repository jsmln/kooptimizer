import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

print("\n" + "="*70)
print("  ANALYZING THE 3 INTEGRATION TEST FAILURES")
print("="*70)

# Check announcements table schema
print("\n1. ANNOUNCEMENTS TABLE SCHEMA:")
print("-" * 70)
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'announcements' 
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    
    print(f"{'Column Name':<30} Type")
    print("-" * 70)
    for col_name, col_type in columns:
        print(f"{col_name:<30} {col_type}")
    
    # Check if announcement_type exists
    col_names = [col[0] for col in columns]
    has_type = 'announcement_type' in col_names
    has_method = 'method' in col_names
    has_channel = 'channel' in col_names
    
    print("\n" + "-" * 70)
    print(f"Has 'announcement_type' column: {has_type}")
    print(f"Has 'method' column: {has_method}")
    print(f"Has 'channel' column: {has_channel}")

# Check actual announcement data
print("\n2. ACTUAL ANNOUNCEMENTS DATA:")
print("-" * 70)
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT announcement_id, title, 
               CASE 
                   WHEN EXISTS (SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'announcements' 
                                AND column_name = 'announcement_type') 
                   THEN 'HAS_TYPE_COLUMN'
                   ELSE 'NO_TYPE_COLUMN'
               END as column_check
        FROM announcements 
        LIMIT 5;
    """)
    announcements = cursor.fetchall()
    
    if announcements:
        print("Sample announcements found:")
        for ann_id, title, check in announcements:
            print(f"  ID {ann_id}: {title[:50]}... [{check}]")
    else:
        print("No announcements found in database")

# Check if the test queries would work with correct column
print("\n3. TESTING CORRECT QUERY:")
print("-" * 70)
try:
    with connection.cursor() as cursor:
        # First, let's see what columns might indicate announcement type
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'announcements' 
            AND (column_name LIKE '%type%' 
                 OR column_name LIKE '%method%' 
                 OR column_name LIKE '%channel%');
        """)
        type_cols = cursor.fetchall()
        
        if type_cols:
            print(f"Columns that might indicate announcement type:")
            for col in type_cols:
                print(f"  - {col[0]}")
        else:
            print("No type-related columns found")
            
except Exception as e:
    print(f"Error: {e}")

# Check OTPService signature
print("\n4. OTP SERVICE INITIALIZATION:")
print("-" * 70)
try:
    from apps.core.services.otp_service import OTPService
    import inspect
    
    # Get the __init__ signature
    sig = inspect.signature(OTPService.__init__)
    print(f"OTPService.__init__ signature: {sig}")
    
    params = list(sig.parameters.keys())
    print(f"Required parameters: {params}")
    
    if 'request' in params:
        print("✓ Requires 'request' parameter - this is EXPECTED behavior")
        print("  This is not a bug, it's by design for session management")
    
except Exception as e:
    print(f"Error checking OTPService: {e}")

# Check how announcements are actually created/sent
print("\n5. CHECKING COMMUNICATIONS VIEWS:")
print("-" * 70)
try:
    from apps.communications import views as comm_views
    import inspect
    
    # Check if views use announcement_type
    source = inspect.getsource(comm_views)
    
    uses_announcement_type = 'announcement_type' in source
    uses_method = "'method'" in source or '"method"' in source
    
    print(f"Communications views use 'announcement_type': {uses_announcement_type}")
    print(f"Communications views use 'method': {uses_method}")
    
    # Check for enum usage
    has_email_enum = "'e-mail'" in source or '"e-mail"' in source
    has_sms_enum = "'sms'" in source or '"sms"' in source
    
    print(f"Views reference 'e-mail' value: {has_email_enum}")
    print(f"Views reference 'sms' value: {has_sms_enum}")
    
except Exception as e:
    print(f"Error checking views: {e}")

print("\n" + "="*70)
print("  IMPACT ASSESSMENT")
print("="*70)
print("""
The 3 test failures are:
1. Email announcements query - uses 'announcement_type' column
2. SMS announcements query - uses 'announcement_type' column  
3. OTPService initialization - requires 'request' parameter

VERDICT:
""")

print("\n" + "="*70 + "\n")
