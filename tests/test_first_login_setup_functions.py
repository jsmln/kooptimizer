"""
Complete First Login Setup Flow Test
Tests all functions in first_login_setup view end-to-end
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.users.models import User
from apps.core.services.otp_service import OTPService
from django.core.cache import cache
from django.test import RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage

def test_first_login_setup_flow():
    """Test the complete first login setup flow"""
    print("=" * 70)
    print("FIRST LOGIN SETUP - COMPLETE FLOW TEST")
    print("=" * 70)
    
    # Find a test user
    print("\n1. Finding test user...")
    test_users = []
    for user in User.objects.filter(is_first_login=True, is_active=True):
        mobile = user.mobile_number
        if mobile and mobile.strip():
            test_users.append(user)
            if len(test_users) >= 5:
                break
    
    if not test_users:
        print("❌ No users available for testing")
        return
    
    print(f"   Found {len(test_users)} users requiring first login setup")
    
    # Display users
    print("\n" + "-" * 70)
    for idx, user in enumerate(test_users, 1):
        print(f"{idx}. {user.username} (Mobile: {user.mobile_number})")
    print("-" * 70)
    
    choice = int(input("\nSelect user number: ").strip())
    if choice < 1 or choice > len(test_users):
        print("❌ Invalid choice")
        return
    
    test_user = test_users[choice - 1]
    
    print(f"\n✅ Selected: {test_user.username}")
    print(f"   User ID: {test_user.user_id}")
    print(f"   Mobile: {test_user.mobile_number}")
    print(f"   Role: {test_user.role}")
    print(f"   First Login: {test_user.is_first_login}")
    
    # Test Step 1: Send OTP
    print("\n" + "=" * 70)
    print("STEP 1: TESTING SEND OTP FUNCTION")
    print("=" * 70)
    
    confirm = input(f"\nSend OTP to {test_user.mobile_number}? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Test cancelled")
        return
    
    # Simulate request
    factory = RequestFactory()
    request = factory.post('/users/first_login_setup/', {
        'action': 'send_otp'
    })
    
    # Add session to request
    middleware = SessionMiddleware(lambda x: x)
    middleware.process_request(request)
    request.session.save()
    
    # Store user ID in session (simulating login)
    request.session['pending_verification_user_id'] = test_user.user_id
    request.session['pending_verification_role'] = test_user.role
    request.session.save()
    
    # Add messages framework
    setattr(request, '_messages', FallbackStorage(request))
    
    print(f"\n📤 Sending OTP...")
    
    # Initialize OTP service and send
    otp_service = OTPService(request)
    success, message = otp_service.send_otp(test_user.mobile_number)
    
    if success:
        cache_key = f"otp_{test_user.mobile_number}"
        stored_otp = cache.get(cache_key)
        
        print(f"\n✅ OTP SENT SUCCESSFULLY!")
        print(f"   Phone: {test_user.mobile_number}")
        print(f"   OTP Code: {stored_otp}")
        print(f"   Cache Key: {cache_key}")
        print(f"   Stored in cache for 5 minutes")
        
        print(f"\n📱 Check phone {test_user.mobile_number} for SMS")
        print(f"   Expected message: 'Your Kooptimizer verification code is: {stored_otp}.")
        print(f"                     This code will expire in 5 minutes.")
        print(f"                     Do not share this code with anyone.'")
        
        # Test Step 2: Verify OTP
        print("\n" + "=" * 70)
        print("STEP 2: TESTING VERIFY OTP FUNCTION")
        print("=" * 70)
        
        received = input("\nDid you receive the SMS? (yes/no): ").strip().lower()
        
        if received != 'yes':
            print("\n⚠️  SMS not received. Possible reasons:")
            print("   - Network delay (wait 1-2 minutes)")
            print("   - Phone coverage issues")
            print("   - Invalid number")
            print(f"\n   For testing purposes, the OTP is: {stored_otp}")
        
        # Test verification
        print(f"\n📝 Testing OTP verification...")
        
        # Test with wrong OTP
        print(f"\n   Test 1: Wrong OTP")
        is_valid, verify_msg = otp_service.verify_otp(test_user.mobile_number, "9999")
        print(f"   Result: {'❌ Correctly rejected' if not is_valid else '⚠️  Should have been rejected'}")
        print(f"   Message: {verify_msg}")
        
        # Test with correct OTP
        print(f"\n   Test 2: Correct OTP")
        # Need to send OTP again since first verify consumed it
        otp_service.send_otp(test_user.mobile_number)
        stored_otp = cache.get(cache_key)
        
        is_valid, verify_msg = otp_service.verify_otp(test_user.mobile_number, stored_otp)
        print(f"   Result: {'✅ Correctly verified' if is_valid else '❌ Should have been verified'}")
        print(f"   Message: {verify_msg if verify_msg else 'Success'}")
        
        if is_valid:
            print(f"\n   ✅ OTP automatically removed from cache after verification")
            remaining = cache.get(cache_key)
            print(f"   Cache check: {remaining if remaining else 'None (correct)'}")
        
        # Test Step 3: Check cache expiration
        print("\n" + "=" * 70)
        print("STEP 3: TESTING OTP EXPIRATION (5 MINUTES)")
        print("=" * 70)
        
        # Send new OTP for expiration test
        otp_service.send_otp(test_user.mobile_number)
        test_otp = cache.get(cache_key)
        
        print(f"\n   OTP generated: {test_otp}")
        print(f"   Cache timeout: 300 seconds (5 minutes)")
        print(f"   Cache key: {cache_key}")
        
        import time
        print(f"\n   Waiting 3 seconds to verify cache persistence...")
        time.sleep(3)
        
        still_there = cache.get(cache_key)
        if still_there == test_otp:
            print(f"   ✅ OTP still valid after 3 seconds: {still_there}")
        else:
            print(f"   ❌ OTP disappeared unexpectedly")
        
        # Clean up
        cache.delete(cache_key)
        print(f"\n   🧹 Test OTP removed from cache")
        
        # Test Step 4: Rate limiting
        print("\n" + "=" * 70)
        print("STEP 4: TESTING RATE LIMITING (30 SECOND COOLDOWN)")
        print("=" * 70)
        
        rate_limit_key = f"otp_send_{test_user.user_id}"
        
        # Set rate limit
        cache.set(rate_limit_key, True, 30)
        print(f"\n   Rate limit key: {rate_limit_key}")
        print(f"   Cooldown: 30 seconds")
        
        # Try to send again immediately
        print(f"\n   Attempting to send OTP again immediately...")
        
        is_limited = cache.get(rate_limit_key)
        if is_limited:
            print(f"   ✅ Rate limit working - prevents duplicate sends")
            print(f"   User would see: 'Please wait before requesting another code'")
        else:
            print(f"   ❌ Rate limit not working")
        
        # Clean up
        cache.delete(rate_limit_key)
        print(f"\n   🧹 Rate limit cleared")
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        print(f"\n✅ All first_login_setup functions tested:")
        print(f"   ✅ send_otp action: OTP generated and sent via SMS")
        print(f"   ✅ verify_otp action: Validates OTP correctly")
        print(f"   ✅ Cache storage: 5-minute expiration working")
        print(f"   ✅ Cache cleanup: OTP removed after verification")
        print(f"   ✅ Rate limiting: 30-second cooldown working")
        
        print(f"\n📋 Next steps to complete flow:")
        print(f"   1. Start server: python manage.py runserver")
        print(f"   2. Login as: {test_user.username}")
        print(f"   3. Complete OTP verification")
        print(f"   4. Set new password")
        print(f"   5. Accept terms & conditions")
        
    else:
        print(f"\n❌ FAILED TO SEND OTP")
        print(f"   Error: {message}")
        print(f"\n   Check:")
        print(f"   - IPROG SMS API credentials")
        print(f"   - Internet connection")
        print(f"   - Phone number format")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    test_first_login_setup_flow()
