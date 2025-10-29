# import http.client
# import json
# from django.conf import settings
# import logging

# logger = logging.getLogger(__name__)

# class OTPService:
#     def __init__(self):
#         self.api_key = settings.INFOBIP['API_KEY']
#         self.base_url = settings.INFOBIP['BASE_URL']
#         self.app_id = settings.INFOBIP['APPLICATION_ID']
#         self.sender_id = settings.INFOBIP['SENDER_ID']
        
#     def _get_connection(self):
#         return http.client.HTTPSConnection(self.base_url)
    
#     def _get_headers(self):
#         return {
#             'Authorization': f'App {self.api_key}',
#             'Content-Type': 'application/json',
#             'Accept': 'application/json'
#         }
    
#     def send_otp(self, mobile_number):
#         """
#         Send OTP to the given phone number
#         Returns: (pin_id, success, error_message)
#         """
#         try:
#             conn = self._get_connection()
#             payload = json.dumps({
#                 "applicationId": self.app_id,
#                 "from": self.sender_id,
#                 "to": mobile_number
#             })
            
#             conn.request("POST", "/2fa/2/pin", payload, self._get_headers())
#             response = conn.getresponse()
#             data = json.loads(response.read().decode("utf-8"))
            
#             if response.status == 200:
#                 return data.get('pinId'), True, None
#             else:
#                 error_msg = data.get('requestError', {}).get('serviceException', {}).get('text', 'Unknown error')
#                 return None, False, error_msg
                
#         except Exception as e:
#             logger.error(f"Error sending OTP: {str(e)}")
#             return None, False, str(e)
#         finally:
#             if 'conn' in locals():
#                 conn.close()
    
#     def verify_otp(self, pin_id, pin_code):
#         """
#         Verify the OTP code
#         Returns: (success, error_message)
#         """
#         try:
#             conn = self._get_connection()
#             payload = json.dumps({
#                 "pin": pin_code
#             })
            
#             conn.request("POST", f"/2fa/2/pin/{pin_id}/verify", payload, self._get_headers())
#             response = conn.getresponse()
#             data = json.loads(response.read().decode("utf-8"))
            
#             if response.status == 200:
#                 return True, None
#             else:
#                 error_msg = data.get('requestError', {}).get('serviceException', {}).get('text', 'Invalid PIN')
#                 return False, error_msg
                
#         except Exception as e:
#             logger.error(f"Error verifying OTP: {str(e)}")
#             return False, str(e)
#         finally:
#             if 'conn' in locals():
#                 conn.close()

import requests
import random
from datetime import datetime, timedelta
from django.conf import settings

class OTPService:
    """
    Service to generate, send, and verify OTPs using the session
    and the IPROG SMS API.
    """

    def __init__(self, request):
        """
        Takes the Django request object to get access to the session.
        """
        self.session = request.session

    def _generate_pin(self, length=4):
        """Generates a random numerical pin."""
        return str(random.randint(10**(length - 1), (10**length) - 1))

    def send_otp(self, mobile_number, message_template="Your OTP is: {pin}"):
        """
        Generates, stores, and sends an OTP.
        """
        try:
            # 1. Generate and store the pin in the session
            pin = self._generate_pin()
            self.session['otp_pin'] = pin
            
            # Set a 5-minute expiry
            expiry_time = (datetime.now() + timedelta(minutes=5)).isoformat()
            self.session['otp_expiry'] = expiry_time

            # 2. Prepare and send the SMS via IPROG API
            url = settings.IPROG_SMS['API_URL']
            message = message_template.format(pin=pin)
            
            data = {
                'api_token': settings.IPROG_SMS['API_TOKEN'],
                'message': message,
                'phone_number': mobile_number  # e.g., '639171071234'
            }

            response = requests.post(url, data=data)
            response.raise_for_status() # Raise an error for bad responses (4xx or 5xx)

            # 3. Return success
            # We don't have a 'pin_id' anymore, so we just return success
            return True, None

        except requests.exceptions.RequestException as e:
            return False, str(e)
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def verify_otp(self, provided_pin):
        """
        Verifies the pin provided by the user against the one in the session.
        """
        stored_pin = self.session.get('otp_pin')
        expiry_str = self.session.get('otp_expiry')

        if not stored_pin or not expiry_str:
            return False, "OTP session expired or not found. Please request a new one."

        # Check for expiry
        if datetime.fromisoformat(expiry_str) < datetime.now():
            self._clear_otp() # Clean up session
            return False, "OTP has expired. Please request a new one."

        # Check for match
        if stored_pin != provided_pin:
            return False, "Invalid OTP code."

        # Success! Clear the OTP from the session
        self._clear_otp()
        return True, None

    def _clear_otp(self):
        """Removes OTP data from the session."""
        if 'otp_pin' in self.session:
            del self.session['otp_pin']
        if 'otp_expiry' in self.session:
            del self.session['otp_expiry']