"""
Test OTP Functionality
Tests the OTPService to ensure it works correctly with IPROG_SMS
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.core.services.otp_service import OTPService
from django.core.cache import cache
import time

def test_otp_service():
    print("=" * 60)
    print("OTP SERVICE TEST")
    print("=" * 60)
    
    # Test phone number (you can change this to a real number for actual testing)
    test_phone = "09123456789"
    
    print(f"\n1. Testing OTP Generation and Storage")
    print(f"   Phone: {test_phone}")
    
    # Initialize OTP Service (without request since we're testing directly)
    otp_service = OTPService()
    
    # Generate and send OTP
    print(f"\n2. Sending OTP...")
    try:
        success, message = otp_service.send_otp(test_phone)
        print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"   Message: {message}")
        
        if success:
            # Check if OTP is stored in cache
            cache_key = f"otp_{test_phone}"
            stored_otp = cache.get(cache_key)
            
            print(f"\n3. Cache Storage Verification")
            print(f"   Cache Key: {cache_key}")
            print(f"   Stored OTP: {stored_otp if stored_otp else 'NOT FOUND'}")
            
            if stored_otp:
                print(f"\n4. Testing OTP Verification (Valid Code)")
                is_valid, verify_msg = otp_service.verify_otp(test_phone, stored_otp)
                print(f"   Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
                print(f"   Message: {verify_msg}")
                
                # Test with wrong OTP
                print(f"\n5. Testing OTP Verification (Invalid Code)")
                is_valid, verify_msg = otp_service.verify_otp(test_phone, "9999")
                print(f"   Result: {'✅ REJECTED' if not is_valid else '❌ UNEXPECTEDLY VALID'}")
                print(f"   Message: {verify_msg}")
                
                # Check cache expiration time
                print(f"\n6. Cache TTL Verification")
                # Re-generate OTP to test TTL
                otp_service.send_otp(test_phone)
                ttl = cache.ttl(cache_key)
                print(f"   TTL (seconds): {ttl}")
                print(f"   Expected: ~300 seconds (5 minutes)")
                
                if 290 <= ttl <= 305:
                    print(f"   Status: ✅ TTL is correct")
                else:
                    print(f"   Status: ⚠️ TTL might be incorrect")
            else:
                print(f"   ❌ OTP was not stored in cache!")
                
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    
    # Cleanup
    cache.delete(f"otp_{test_phone}")
    print("\n✅ Cache cleaned up")

def test_configuration():
    """Test IPROG_SMS configuration"""
    print("\n" + "=" * 60)
    print("CONFIGURATION TEST")
    print("=" * 60)
    
    from django.conf import settings
    
    print("\n1. IPROG_SMS Configuration:")
    if hasattr(settings, 'IPROG_SMS'):
        iprog_config = settings.IPROG_SMS
        print(f"   ✅ IPROG_SMS found in settings")
        print(f"   API_TOKEN: {'*' * 10}{iprog_config['API_TOKEN'][-4:] if iprog_config.get('API_TOKEN') else 'NOT SET'}")
        print(f"   API_URL: {iprog_config.get('API_URL', 'NOT SET')}")
        print(f"   API_URL_BULK: {iprog_config.get('API_URL_BULK', 'NOT SET')}")
    else:
        print(f"   ❌ IPROG_SMS not found in settings!")
    
    print("\n2. Cache Configuration:")
    cache_backend = settings.CACHES['default']['BACKEND']
    cache_location = settings.CACHES['default']['LOCATION']
    print(f"   Backend: {cache_backend}")
    print(f"   Location: {cache_location}")
    
    if 'DatabaseCache' in cache_backend:
        print(f"   ✅ Using Database Cache")
    
    print("\n3. Testing Cache Connectivity:")
    test_key = "test_connection_key"
    test_value = "test_value_123"
    
    try:
        cache.set(test_key, test_value, 10)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            print(f"   ✅ Cache is working correctly")
        else:
            print(f"   ❌ Cache read/write mismatch")
        
        cache.delete(test_key)
    except Exception as e:
        print(f"   ❌ Cache error: {str(e)}")
    
    print("=" * 60)

if __name__ == "__main__":
    # Run configuration test first
    test_configuration()
    
    print("\n\n")
    
    # Then run OTP service test
    test_otp_service()
    
    print("\n\n📝 NOTE:")
    print("   - If you want to test actual SMS sending, replace the test phone")
    print("     number with a real one in the script.")
    print("   - The OTP will be sent via IPROG SMS API.")
    print("   - Check your phone to receive the verification code.")
