"""
Test OTP SMS Sending
Tests if OTP SMS actually sends via IPROG SMS API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.core.services.otp_service import OTPService
from django.core.cache import cache

def test_real_sms_send():
    """Test sending actual SMS"""
    print("=" * 60)
    print("OTP SMS SENDING TEST")
    print("=" * 60)
    
    # IMPORTANT: Replace with YOUR real phone number to test
    # Format: 09XXXXXXXXX (Philippine mobile number)
    test_phone = input("\nEnter your phone number (09XXXXXXXXX) to test SMS: ").strip()
    
    if not test_phone or len(test_phone) != 11 or not test_phone.startswith('09'):
        print("❌ Invalid phone number format! Use: 09XXXXXXXXX")
        return
    
    confirm = input(f"\n⚠️  This will send an SMS to {test_phone}. Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Test cancelled")
        return
    
    print(f"\n📱 Sending OTP to {test_phone}...")
    print("-" * 60)
    
    otp_service = OTPService()
    
    try:
        success, message = otp_service.send_otp(test_phone)
        
        if success:
            # Get the OTP from cache to show user
            cache_key = f"otp_{test_phone}"
            stored_otp = cache.get(cache_key)
            
            print(f"\n✅ SMS SENT SUCCESSFULLY!")
            print(f"\nDetails:")
            print(f"   Phone: {test_phone}")
            print(f"   OTP Code: {stored_otp}")
            print(f"   Message: Your Kooptimizer verification code is: {stored_otp}.")
            print(f"            This code will expire in 5 minutes.")
            print(f"            Do not share this code with anyone.")
            
            print(f"\n📱 Check your phone for the SMS!")
            print(f"\n" + "-" * 60)
            
            # Ask user to verify
            received = input("\nDid you receive the SMS? (yes/no): ").strip().lower()
            
            if received == 'yes':
                entered_code = input("Enter the OTP code you received: ").strip()
                
                is_valid, verify_msg = otp_service.verify_otp(test_phone, entered_code)
                
                if is_valid:
                    print(f"\n✅ OTP VERIFICATION SUCCESSFUL!")
                    print(f"   The OTP system is working perfectly!")
                else:
                    print(f"\n❌ OTP VERIFICATION FAILED")
                    print(f"   Message: {verify_msg}")
                    print(f"   Expected: {stored_otp}")
                    print(f"   Received: {entered_code}")
            else:
                print(f"\n⚠️  SMS might not have been delivered")
                print(f"   Possible reasons:")
                print(f"   - Network delay (check again in a minute)")
                print(f"   - Invalid phone number")
                print(f"   - IPROG SMS API issues")
                print(f"   - Insufficient SMS credits")
            
            # Cleanup
            cache.delete(cache_key)
            print(f"\n✅ Cache cleaned up")
            
        else:
            print(f"\n❌ FAILED TO SEND SMS")
            print(f"   Error: {message}")
            print(f"\n   Possible causes:")
            print(f"   - Invalid API token")
            print(f"   - Network connectivity issues")
            print(f"   - IPROG SMS API is down")
            print(f"   - Insufficient credits")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_real_sms_send()
