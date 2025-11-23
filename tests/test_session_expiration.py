"""
Test Session Expiration on Browser Close
This script helps verify how quickly sessions expire after browser close
"""
import sys
import os
import django
import time
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.conf import settings

print("="*80)
print("SESSION EXPIRATION TEST")
print("="*80)

# Display current settings
print(f"\nCurrent Session Settings:")
print(f"  SESSION_EXPIRE_AT_BROWSER_CLOSE: {settings.SESSION_EXPIRE_AT_BROWSER_CLOSE}")
print(f"  SESSION_COOKIE_AGE: {settings.SESSION_COOKIE_AGE} seconds ({settings.SESSION_COOKIE_AGE // 60} minutes)")
print(f"  SESSION_SAVE_EVERY_REQUEST: {settings.SESSION_SAVE_EVERY_REQUEST}")
print(f"  SESSION_ENGINE: {settings.SESSION_ENGINE}")

# Check active sessions
print(f"\n{'='*80}")
print("ACTIVE SESSIONS IN DATABASE")
print("="*80)

sessions = Session.objects.all()
print(f"\nTotal sessions in database: {sessions.count()}")

if sessions.count() > 0:
    print("\nSession Details:")
    for i, session in enumerate(sessions[:10], 1):  # Show first 10
        session_data = session.get_decoded()
        user_id = session_data.get('user_id', 'N/A')
        role = session_data.get('role', 'N/A')
        last_activity = session_data.get('last_activity', 'N/A')
        
        if last_activity != 'N/A':
            last_activity_time = datetime.fromtimestamp(last_activity)
            age_seconds = time.time() - last_activity
            age_minutes = int(age_seconds / 60)
            print(f"\n  [{i}] Session Key: {session.session_key[:20]}...")
            print(f"      User ID: {user_id}")
            print(f"      Role: {role}")
            print(f"      Last Activity: {last_activity_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      Age: {age_minutes} minutes, {int(age_seconds % 60)} seconds")
            print(f"      Expires: {session.expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if session should be expired
            if age_seconds > settings.SESSION_COOKIE_AGE:
                print(f"      Status: ⚠️ EXPIRED (inactive for {age_minutes} minutes)")
            else:
                remaining = settings.SESSION_COOKIE_AGE - age_seconds
                print(f"      Status: ✓ ACTIVE (expires in {int(remaining/60)} minutes)")
        else:
            print(f"\n  [{i}] Session Key: {session.session_key[:20]}...")
            print(f"      User ID: {user_id}")
            print(f"      Role: {role}")
            print(f"      Last Activity: Not set (old session)")
            print(f"      Expires: {session.expire_date.strftime('%Y-%m-%d %H:%M:%S')}")

print("\n" + "="*80)
print("HOW SESSION EXPIRATION WORKS")
print("="*80)

print("""
When Browser/Tab Closes:
========================
1. SESSION_EXPIRE_AT_BROWSER_CLOSE = True
   → Cookie is marked as "session cookie" (not persistent)
   → Browser IMMEDIATELY deletes cookie from memory when closed
   → Time to expire: 0 seconds (instant)

2. Database Session Entry:
   → Still exists in database temporarily
   → Will be cleaned up by: python manage.py clearsessions
   → Or expires after SESSION_COOKIE_AGE (15 minutes of inactivity)

3. When User Returns:
   → No session cookie in browser
   → Middleware checks for user_id in session → Not found
   → Redirects to login page ✓

Session Validation in Middleware:
=================================
1. Checks if 'last_activity' timestamp exists in session
2. If missing → Session is stale/restored → Force logout
3. If exists → Validates age against SESSION_COOKIE_AGE
4. If expired → Clear session and redirect to login

Current Protection:
===================
✓ Session cookie expires on browser close (instant)
✓ Middleware validates session freshness on every request
✓ Missing 'last_activity' forces re-authentication
✓ Inactivity timeout: 15 minutes
✓ Cache headers prevent page caching
✓ beforeunload confirmation prompts user before closing
""")

print("\n" + "="*80)
print("MANUAL TEST PROCEDURE")
print("="*80)

print("""
To Test Session Expiration:
============================

1. Clear browser cookies (Ctrl+Shift+Delete)
2. Login to the application
3. Note the time
4. Close browser COMPLETELY (not just tab)
5. Wait 5 seconds
6. Reopen browser
7. Paste URL: http://127.0.0.1:8000/account_management/account_management/

Expected Result:
→ Redirected to login page
→ Session cookie was deleted on browser close (0 seconds)
→ No valid session found in browser

If Still Logged In:
→ Browser is restoring session cookies (some browsers do this)
→ Middleware will catch missing 'last_activity' and force logout
→ Or session will expire after 15 minutes of inactivity
""")

print("\n" + "="*80)
print("CLEANUP COMMANDS")
print("="*80)

print("""
Clear all sessions from database:
    python manage.py clearsessions

Clear specific old sessions (Django automatically removes expired ones):
    Django's SessionMiddleware handles this automatically
""")

print("\n" + "="*80)
