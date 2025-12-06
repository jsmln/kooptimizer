"""
Detailed OTP SMS Sending Test with API Response
Shows the actual IPROG SMS API response to diagnose delivery issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.conf import settings
import requests
import random

def test_iprog_sms_api_directly():
    """Test IPROG SMS API directly to see response"""
    print("=" * 60)
    print("IPROG SMS API DIRECT TEST")
    print("=" * 60)
    
    # Get API credentials
    api_token = settings.IPROG_SMS.get('API_TOKEN')
    api_url = settings.IPROG_SMS.get('API_URL')
    
    print(f"\nAPI Configuration:")
    print(f"   API URL: {api_url}")
    print(f"   API Token: {'*' * 10}{api_token[-4:] if api_token else 'NOT SET'}")
    
    # Test phone number
    test_phone = input("\nEnter phone number to test (09XXXXXXXXX): ").strip()
    
    if not test_phone or len(test_phone) != 11:
        print("❌ Invalid phone number")
        return
    
    confirm = input(f"\n⚠️  Send test OTP to {test_phone}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Test cancelled")
        return
    
    # Generate test OTP
    otp_code = str(random.randint(1000, 9999))
    message = f"Your Kooptimizer verification code is: {otp_code}. This code will expire in 5 minutes. Do not share this code with anyone."
    
    print(f"\n📱 Sending SMS...")
    print(f"   Phone: {test_phone}")
    print(f"   OTP: {otp_code}")
    print(f"   Message: {message[:50]}...")
    print("\n" + "-" * 60)
    
    try:
        # Prepare request - using same format as SmsService
        payload = {
            'api_token': api_token,
            'message': message,
            'phone_number': test_phone
        }
        
        print(f"\n📤 Request Details:")
        print(f"   URL: {api_url}")
        print(f"   Method: POST (form data)")
        print(f"   Payload: {{'api_token': '***', 'message': '{message[:30]}...', 'phone_number': '{test_phone}'}}")
        
        # Send request - using 'data' not 'json'
        response = requests.post(api_url, data=payload, timeout=10)
        
        print(f"\n📥 Response Details:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Status: {'✅ SUCCESS' if response.status_code == 200 else '❌ FAILED'}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print(f"   Response JSON:")
            import json
            print(json.dumps(response_data, indent=6))
            
            # Check if API response status is 200
            if response_data.get('status') == 200:
                print("\n✅ IPROG API CONFIRMED SUCCESS!")
                print(f"   API Message: {response_data.get('message', 'SMS queued')}")
            else:
                print(f"\n⚠️  IPROG API returned error status: {response_data.get('status')}")
                print(f"   API Message: {response_data.get('message')}")
        except:
            print(f"   Response Text: {response.text}")
        
        print("\n" + "-" * 60)
        
        if response.status_code == 200:
            print("\n✅ SMS API REQUEST SUCCESSFUL!")
            print(f"\nThe OTP {otp_code} should arrive at {test_phone}")
            print("\nPossible reasons if not received:")
            print("   1. Network delay (can take 30 seconds to 2 minutes)")
            print("   2. Phone number format issue (should be 09XXXXXXXXX)")
            print("   3. Recipient's phone is off/out of coverage")
            print("   4. Telecom network issues")
            print("   5. Number is not registered/invalid")
            
            received = input("\nWait 1-2 minutes, then confirm - Did you receive the SMS? (yes/no): ").strip().lower()
            
            if received == 'yes':
                print("\n🎉 SUCCESS! OTP SMS delivery is working!")
                print("   The first_login_setup flow will work correctly.")
            else:
                print("\n⚠️  SMS not received despite successful API response")
                print("   This is likely a telecom/network issue, not a code issue.")
                print("   Try with a different phone number or check with your provider.")
        else:
            print("\n❌ SMS API REQUEST FAILED!")
            print(f"   HTTP Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   Error: Invalid API token or authentication failed")
                print("   Solution: Check IPROG_SMS_API_TOKEN in your .env file")
            elif response.status_code == 400:
                print("   Error: Bad request - invalid parameters")
                print("   Solution: Check phone number format and message content")
            elif response.status_code == 429:
                print("   Error: Rate limit exceeded")
                print("   Solution: Wait a few minutes and try again")
            elif response.status_code == 402:
                print("   Error: Insufficient credits")
                print("   Solution: Top up your IPROG SMS account")
            else:
                print(f"   Error: Unexpected status code {response.status_code}")
                
    except requests.exceptions.Timeout:
        print("\n❌ REQUEST TIMEOUT")
        print("   The API did not respond within 10 seconds")
        print("   Check your internet connection")
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR")
        print("   Could not connect to IPROG SMS API")
        print("   Check your internet connection")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_iprog_sms_api_directly()
