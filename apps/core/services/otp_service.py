import requests
import random
import string
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

    def send_otp(self, mobile_number, message_template="Welcome to KoopTimizer! Your verification code is {pin}. Do not share this with anyone."):
        """
        Generates, stores, and sends an OTP.
        """
        print(f"--- OTP SERVICE STARTED ---") # DEBUG
        try:
            # 1. Generate and store the pin in the session
            pin = self._generate_pin()
            self.session['otp_pin'] = pin
            
            # Set a 5-minute expiry
            expiry_time = (datetime.now() + timedelta(minutes=5)).isoformat()
            self.session['otp_expiry'] = expiry_time
            
            # Save session immediately to ensure persistence
            self.session.save()

            print(f"✅ Generated PIN: {pin}") # DEBUG: See the pin in console
            print(f"✅ Target Number: {mobile_number}") # DEBUG

            # 2. Prepare and send the SMS via IPROG API
            url = settings.IPROG_SMS.get('API_URL')
            api_token = settings.IPROG_SMS.get('API_TOKEN')
            
            if not url or not api_token:
                print("❌ ERROR: IPROG settings missing in settings.py")
                return False, "System configuration error."

            message = message_template.format(pin=pin)
            
            data = {
                'api_token': api_token,
                'message': message,
                'phone_number': mobile_number
            }

            print(f"📡 Sending Request to: {url}") # DEBUG
            
            # Added timeout to prevent hanging
            response = requests.post(url, data=data, timeout=15)
            
            print(f"📩 API Response Code: {response.status_code}") # DEBUG
            print(f"📩 API Response Body: {response.text}") # DEBUG

            response.raise_for_status() # Raise an error for bad responses (4xx or 5xx)

            return True, None

        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {e}") # DEBUG
            return False, "Network error sending SMS."
        except Exception as e:
            print(f"❌ Unexpected Error: {e}") # DEBUG
            return False, f"An unexpected error occurred: {e}"

    def verify_otp(self, provided_pin):
        """
        Verifies the pin provided by the user against the one in the session.
        """
        stored_pin = self.session.get('otp_pin')
        expiry_str = self.session.get('otp_expiry')

        print(f"🔍 Verifying OTP: Input='{provided_pin}' vs Stored='{stored_pin}'") # DEBUG

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
        self.session.save()