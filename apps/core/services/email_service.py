# apps/core/services/email_service.py
import sib_api_v3_sdk # pyright: ignore[reportMissingImports]
from sib_api_v3_sdk.rest import ApiException # pyright: ignore[reportMissingImports]
from django.conf import settings

class EmailService:
    def __init__(self):
        self.configuration = sib_api_v3_sdk.Configuration()
        self.configuration.api_key['api-key'] = settings.BREVO_API_KEY
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(self.configuration))

    def send_bulk_announcement(self, announcement_id, subject, html_content, recipients_list):
        """
        recipients_list: list of strings ['email1@test.com', 'email2@test.com']
        """
        if not recipients_list:
            return False, "No valid email recipients found."

        sender = {"name": settings.DEFAULT_FROM_NAME, "email": settings.DEFAULT_FROM_EMAIL}
        
        # Brevo Transactional API limits 'to' recipients. 
        # For bulk, it is best to send individually or use BCC to hide recipients from each other.
        # Here we use BCC for efficiency, or you can loop to send individual emails.
        
        # Option A: Send as BCC (One API call, recipients don't see each other)
        # Limit: Brevo usually allows 50-99 recipients per call in BCC. 
        # If you have hundreds, you must chunk this list.
        
        chunk_size = 45 
        chunks = [recipients_list[i:i + chunk_size] for i in range(0, len(recipients_list), chunk_size)]

        errors = []

        for chunk in chunks:
            # Convert list of strings to list of objects for Brevo
            bcc_emails = [{"email": email} for email in chunk]
            
            # We must have at least one "To" address. Usually the sender or a generic admin email.
            to = [{"email": settings.DEFAULT_FROM_EMAIL, "name": "Announcement Copy"}]

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                bcc=bcc_emails,
                sender=sender,
                subject=subject,
                html_content=html_content,
                tags=["announcement", f"announcement_{announcement_id}"]
            )

            try:
                self.api_instance.send_transac_email(send_smtp_email)
            except ApiException as e:
                errors.append(str(e))

        if errors:
            return False, f"Some batches failed: {', '.join(errors)}"
        
        return True, "Emails sent successfully"