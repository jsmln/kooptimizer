import http.client
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self):
        self.api_key = settings.INFOBIP['API_KEY']
        self.base_url = settings.INFOBIP['BASE_URL']
        self.app_id = settings.INFOBIP['APPLICATION_ID']
        self.sender_id = settings.INFOBIP['SENDER_ID']
        
    def _get_connection(self):
        return http.client.HTTPSConnection(self.base_url)
    
    def _get_headers(self):
        return {
            'Authorization': f'App {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def send_otp(self, phone_number):
        """
        Send OTP to the given phone number
        Returns: (pin_id, success, error_message)
        """
        try:
            conn = self._get_connection()
            payload = json.dumps({
                "applicationId": self.app_id,
                "from": self.sender_id,
                "to": phone_number
            })
            
            conn.request("POST", "/2fa/2/pin", payload, self._get_headers())
            response = conn.getresponse()
            data = json.loads(response.read().decode("utf-8"))
            
            if response.status == 200:
                return data.get('pinId'), True, None
            else:
                error_msg = data.get('requestError', {}).get('serviceException', {}).get('text', 'Unknown error')
                return None, False, error_msg
                
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return None, False, str(e)
        finally:
            if 'conn' in locals():
                conn.close()
    
    def verify_otp(self, pin_id, pin_code):
        """
        Verify the OTP code
        Returns: (success, error_message)
        """
        try:
            conn = self._get_connection()
            payload = json.dumps({
                "pin": pin_code
            })
            
            conn.request("POST", f"/2fa/2/pin/{pin_id}/verify", payload, self._get_headers())
            response = conn.getresponse()
            data = json.loads(response.read().decode("utf-8"))
            
            if response.status == 200:
                return True, None
            else:
                error_msg = data.get('requestError', {}).get('serviceException', {}).get('text', 'Invalid PIN')
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False, str(e)
        finally:
            if 'conn' in locals():
                conn.close()