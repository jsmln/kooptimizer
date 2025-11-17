# core/services/sms_service.py

import requests
from django.conf import settings
from django.db import connection
import logging

# Set up a logger for this service
logger = logging.getLogger(__name__)

class SmsService:
    """
    Service to send bulk SMS announcements via the IPROG SMS API.
    """

    def __init__(self):
        """
        Initializes the service with API credentials from settings.
        """
        try:
            self.api_url = settings.IPROG_SMS['API_URL_BULK']
            self.api_token = settings.IPROG_SMS['API_TOKEN']
        except (AttributeError, KeyError):
            logger.error("IPROG_SMS settings (API_URL_BULK, API_TOKEN) not found.")
            raise ValueError("IPROG_SMS API credentials are not configured.")

    def _get_recipient_numbers(self, announcement_id):
        """
        Calls the stored procedure to get the comma-separated phone list.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_get_sms_recipients(%s)", [announcement_id])
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
        return None

    def send_bulk_announcement(self, announcement_id, message):
        """
        Fetches recipients and sends the bulk SMS.
        
        Returns: (success, message_or_error)
        """
        
        # 1. Get the list of phone numbers from the database
        phone_numbers_str = self._get_recipient_numbers(announcement_id)
        
        if not phone_numbers_str:
            logger.warning(f"No recipients found for announcement_id: {announcement_id}.")
            return False, "No recipients found for this announcement."

        # 2. Prepare and send the SMS via IPROG API
        payload = {
            'api_token': self.api_token,
            'message': message,
            'phone_number': phone_numbers_str
        }

        try:
            response = requests.post(self.api_url, data=payload)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            
            response_data = response.json()
            
            if response_data.get("status") == 200:
                logger.info(f"Successfully queued bulk SMS for announcement_id: {announcement_id}.")
                return True, response_data.get("message", "SMS queued successfully.")
            else:
                logger.error(f"IPROG API error for {announcement_id}: {response_data}")
                return False, response_data.get("message", "An API error occurred.")

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed for announcement_id {announcement_id}: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error in send_bulk_announcement: {e}")
            return False, f"An unexpected error occurred: {e}"