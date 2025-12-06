import requests
import random
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self, request=None):
        self.request = request
        try:
            self.api_url = settings.IPROG_SMS['API_URL']
            self.api_token = settings.IPROG_SMS['API_TOKEN']
        except (AttributeError, KeyError):
            logger.error("IPROG_SMS settings not found.")
            raise ValueError("IPROG_SMS API credentials are not configured.")
    
    def _generate_otp_code(self):
        """Generate a random 4-digit OTP code"""
        return str(random.randint(1000, 9999))
    
    def send_otp(self, phone_number):
        """
        Send OTP to the given phone number using IPROG SMS API
        Returns: (success, error_message)
        """
        try:
            # Generate OTP code
            otp_code = self._generate_otp_code()
            
            # Store OTP in cache for 5 minutes (300 seconds)
            cache_key = f"otp_{phone_number}"
            cache.set(cache_key, otp_code, 300)
            
            # Prepare SMS message with clear expiration notice
            message = f"Your Kooptimizer verification code is: {otp_code}. This code will expire in 5 minutes. Do not share this code with anyone."
            
            # Send via IPROG SMS API using the same format as SmsService
            payload = {
                'api_token': self.api_token,
                'message': message,
                'phone_number': phone_number
            }
            
            response = requests.post(self.api_url, data=payload, timeout=10)
            
            # Check response - IPROG API returns JSON with status field
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    # Check if response status is 200 (success)
                    if response_data.get('status') == 200:
                        logger.info(f"OTP sent successfully to {phone_number}")
                        return True, None
                    else:
                        # API returned error in response body
                        error_msg = response_data.get('message', 'Unknown error')
                        logger.error(f"IPROG SMS API error: {error_msg}")
                        return False, f"SMS service error: {error_msg}"
                except ValueError:
                    # Response is not JSON, assume success
                    logger.info(f"OTP sent successfully to {phone_number}")
                    return True, None
            else:
                error_msg = f"Failed to send OTP: HTTP {response.status_code}"
                logger.error(f"{error_msg} - {response.text}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return False, str(e)
    
    def verify_otp(self, phone_number, otp_code):
        """
        Verify the OTP code against stored value in cache
        Returns: (success, error_message)
        """
        try:
            cache_key = f"otp_{phone_number}"
            stored_otp = cache.get(cache_key)
            
            if not stored_otp:
                return False, "OTP expired or not found. Please request a new one."
            
            if stored_otp == otp_code:
                # OTP is valid, delete it from cache
                cache.delete(cache_key)
                logger.info(f"OTP verified successfully for {phone_number}")
                return True, None
            else:
                return False, "Invalid OTP code. Please try again."
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False, str(e)