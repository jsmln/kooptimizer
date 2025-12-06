"""
Test First Login Setup Flow
Verifies that OTP sends to real user mobile numbers during first login
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.users.models import User
from apps.core.services.otp_service import OTPService
from django.core.cache import cache

def test_first_login_users():
    """Check for users who need first login setup"""
    print("=" * 60)
    print("FIRST LOGIN SETUP - USER CHECK")
    print("=" * 60)
    
    # Find users who haven't completed first login
    all_first_login_users = User.objects.filter(
        is_first_login=True,
        is_active=True
    )
    
    # Filter users with mobile numbers (property, so we filter in Python)
    first_login_users = []
    for user in all_first_login_users:
        mobile = user.mobile_number
        if mobile and mobile.strip():
            first_login_users.append(user)
    
    print(f"\nUsers requiring first login setup: {len(first_login_users)}")
    
    if len(first_login_users) == 0:
        print("\n⚠️  No users found that need first login setup")
        print("   All users may have already completed first login")
        print("   or don't have mobile numbers set")
        return None
    
    print("\n" + "-" * 60)
    print("User Details:")
    print("-" * 60)
    
    for idx, user in enumerate(first_login_users[:5], 1):  # Show first 5
        print(f"\n{idx}. User ID: {user.user_id}")
        print(f"   Username: {user.username}")
        print(f"   Mobile: {user.mobile_number}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   First Login: {user.is_first_login}")
    
    if len(first_login_users) > 5:
        print(f"\n... and {len(first_login_users) - 5} more users")
    
    return first_login_users

def test_otp_send_to_real_user():
    """Test sending OTP to a real user's mobile number"""
    print("\n\n" + "=" * 60)
    print("OTP SENDING TEST - REAL USER")
    print("=" * 60)
    
    users = test_first_login_users()
    
    if not users:
        print("\n❌ Cannot proceed without users requiring first login")
        return
    
    print("\n" + "-" * 60)
    print("SELECT A USER TO TEST OTP SENDING")
    print("-" * 60)
    
    try:
        user_choice = int(input("\nEnter user number (1-5): ").strip())
        
        if user_choice < 1 or user_choice > min(5, len(users)):
            print("❌ Invalid choice")
            return
        
        selected_user = users[user_choice - 1]
        
        print(f"\n📱 Selected User:")
        print(f"   Username: {selected_user.username}")
        print(f"   Mobile: {selected_user.mobile_number}")
        
        confirm = input(f"\n⚠️  Send OTP to {selected_user.mobile_number}? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Test cancelled")
            return
        
        print(f"\n🚀 Sending OTP via IPROG SMS...")
        print("-" * 60)
        
        otp_service = OTPService()
        success, message = otp_service.send_otp(selected_user.mobile_number)
        
        if success:
            cache_key = f"otp_{selected_user.mobile_number}"
            stored_otp = cache.get(cache_key)
            
            print(f"\n✅ OTP SENT SUCCESSFULLY!")
            print(f"\nDetails:")
            print(f"   User: {selected_user.username}")
            print(f"   Phone: {selected_user.mobile_number}")
            print(f"   OTP Code: {stored_otp}")
            print(f"   Cache Key: {cache_key}")
            print(f"   Expiration: 5 minutes (300 seconds)")
            
            print(f"\n📨 SMS Message:")
            print(f"   'Your Kooptimizer verification code is: {stored_otp}.")
            print(f"    This code will expire in 5 minutes.")
            print(f"    Do not share this code with anyone.'")
            
            print(f"\n📱 Check the phone {selected_user.mobile_number} for SMS!")
            print("-" * 60)
            
            received = input("\nDid the user receive the SMS? (yes/no): ").strip().lower()
            
            if received == 'yes':
                print("\n✅ SMS DELIVERY CONFIRMED!")
                
                verify = input("\nTest OTP verification? (yes/no): ").strip().lower()
                
                if verify == 'yes':
                    entered_code = input("Enter the 4-digit OTP received: ").strip()
                    
                    is_valid, verify_msg = otp_service.verify_otp(
                        selected_user.mobile_number, 
                        entered_code
                    )
                    
                    if is_valid:
                        print(f"\n✅ OTP VERIFICATION SUCCESSFUL!")
                        print(f"   Code matched: {entered_code}")
                        print(f"\n🎉 First login setup flow is working perfectly!")
                    else:
                        print(f"\n❌ OTP VERIFICATION FAILED")
                        print(f"   Message: {verify_msg}")
                        print(f"   Expected: {stored_otp}")
                        print(f"   Entered: {entered_code}")
                else:
                    print("\n⏭️  Verification test skipped")
                    # Cleanup
                    cache.delete(cache_key)
                    print("✅ Cache cleaned up")
            else:
                print(f"\n⚠️  SMS NOT RECEIVED")
                print(f"\n   Troubleshooting:")
                print(f"   1. Check if phone number is correct: {selected_user.mobile_number}")
                print(f"   2. Verify IPROG SMS API has credits")
                print(f"   3. Check network signal on receiving phone")
                print(f"   4. Wait a few more seconds (network delay)")
                print(f"   5. Check spam/blocked messages")
                
                # Show the OTP for manual verification
                print(f"\n   For testing, the OTP code is: {stored_otp}")
                
                # Cleanup
                cache.delete(cache_key)
                print("\n✅ Cache cleaned up")
        else:
            print(f"\n❌ FAILED TO SEND OTP")
            print(f"   Error: {message}")
            print(f"\n   Check:")
            print(f"   - IPROG SMS API credentials")
            print(f"   - Internet connectivity")
            print(f"   - SMS API status")
            
    except ValueError:
        print("❌ Invalid input")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

def show_test_instructions():
    """Show instructions for manual testing via browser"""
    print("\n\n" + "=" * 60)
    print("MANUAL BROWSER TEST INSTRUCTIONS")
    print("=" * 60)
    
    print(f"\n📋 To test the complete first login setup flow:")
    print(f"\n1. Start the development server:")
    print(f"   python manage.py runserver")
    
    print(f"\n2. Open browser and go to:")
    print(f"   http://127.0.0.1:8000/users/login/")
    
    print(f"\n3. Login with a user who has is_first_login=True")
    print(f"   (See user list above)")
    
    print(f"\n4. You should be redirected to first login setup with:")
    print(f"   - 'Send Verification Code' button")
    print(f"   - Masked phone number display")
    
    print(f"\n5. Click 'Send Verification Code'")
    print(f"   - OTP will be sent via IPROG SMS")
    print(f"   - Check the user's real mobile phone")
    
    print(f"\n6. Enter the 4-digit code received")
    print(f"   - Input boxes should auto-focus")
    print(f"   - Submit to verify")
    
    print(f"\n7. On success:")
    print(f"   - Password setup form appears")
    print(f"   - User can set new password")
    print(f"   - Accept terms checkbox")
    
    print(f"\n8. Complete password setup")
    print(f"   - User should be redirected to dashboard")
    print(f"   - is_first_login flag updated to False")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_otp_send_to_real_user()
    show_test_instructions()
