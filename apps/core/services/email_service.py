# apps/core/services/email_service.py
import requests
from django.conf import settings
from django.db import connection
from django.template.loader import render_to_string
from typing import Tuple
import html


class EmailService:
    """
    Email service for sending announcements via Brevo API.
    Uses the same implementation as account management credentials.
    """
    
    def send_bulk_announcement(self, announcement_id: int, content: str) -> Tuple[bool, str]:
        """
        Send bulk emails for an announcement to all its recipients.
        
        Args:
            announcement_id: The ID of the announcement
            content: Email body content (plain text, will be converted to HTML)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get announcement details including attachments
            announcement_data = self._get_announcement_data(announcement_id)
            if not announcement_data:
                return False, "Announcement not found"
            
            # Get all officer emails for this announcement
            recipients_list = self._get_announcement_recipients(announcement_id)
            
            if not recipients_list:
                return False, "No valid email recipients found"
            
            # Format content as HTML
            html_content = self._format_html_content(
                announcement_data['title'],
                content,
                announcement_data['sender_name']
            )
            
            # Send using Brevo API
            return self._send_bulk_email(
                subject=announcement_data['title'],
                html_content=html_content,
                recipients_list=recipients_list,
                attachment_data=announcement_data.get('attachment_data')
            )
            
        except Exception as e:
            return False, f"Error sending bulk email: {str(e)}"
    
    def _get_announcement_data(self, announcement_id: int) -> dict:
        """Get announcement title, sender information, and attachments."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        a.title,
                        COALESCE(s.fullname, adm.fullname, 'System') as sender_name,
                        a.attachment,
                        a.attachment_filename,
                        a.attachment_content_type,
                        a.attachment_size
                    FROM announcements a
                    LEFT JOIN staff s ON a.staff_id = s.staff_id
                    LEFT JOIN admin adm ON a.admin_id = adm.admin_id
                    WHERE a.announcement_id = %s
                """, [announcement_id])
                
                row = cursor.fetchone()
                if row:
                    result = {
                        'title': row[0],
                        'sender_name': row[1]
                    }
                    
                    # Add attachment data if exists
                    if row[2] and row[3]:  # attachment and attachment_filename
                        result['attachment_data'] = {
                            'content': row[2],
                            'filenames': row[3],
                            'content_type': row[4],
                            'size': row[5]
                        }
                    
                    return result
            return None
        except Exception as e:
            print(f"Error retrieving announcement data: {e}")
            return None
    
    def _get_announcement_recipients(self, announcement_id: int) -> list:
        """
        Retrieve all officer email addresses for a given announcement.
        Handles both cooperative-level and officer-level recipients.
        Returns list of dicts with 'email' and 'name' keys.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT o.email, o.fullname
                    FROM announcement_officer_recipients aor
                    JOIN officers o ON aor.officer_id = o.officer_id
                    WHERE aor.announcement_id = %s AND o.email IS NOT NULL AND o.email != ''
                    
                    UNION
                    
                    SELECT DISTINCT o.email, o.fullname
                    FROM announcement_recipients ar
                    JOIN officers o ON ar.coop_id = o.coop_id
                    WHERE ar.announcement_id = %s AND o.email IS NOT NULL AND o.email != ''
                """, [announcement_id, announcement_id])
                
                recipients = cursor.fetchall()
            
            # Return list of dicts for Brevo API
            return [
                {'email': email, 'name': name} 
                for email, name in recipients 
                if email
            ]
            
        except Exception as e:
            print(f"Error retrieving recipients: {e}")
            return []
    
    def _send_bulk_email(self, subject: str, html_content: str, recipients_list: list, attachment_data: dict = None) -> Tuple[bool, str]:
        """
        Send email to multiple recipients using Brevo API.
        
        Args:
            subject: Email subject
            html_content: HTML formatted email body
            recipients_list: List of dicts with 'email' and 'name' keys
            attachment_data: Optional dict with 'content', 'filenames', 'content_type', 'size'
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not recipients_list:
            return False, "No valid email recipients found"
        
        # Brevo API configuration
        headers = {
            'accept': 'application/json',
            'api-key': settings.BREVO_API_KEY,
            'content-type': 'application/json'
        }
        
        # Prepare attachments for Brevo (base64 encoded)
        attachments = []
        if attachment_data and attachment_data.get('content') and attachment_data.get('filenames'):
            import base64
            
            # Get filenames (semicolon-separated)
            filenames = attachment_data['filenames'].split(';')
            attachment_bytes = attachment_data['content']
            
            # For combined files, we need to send as a single attachment
            # Using the first filename or a generic name
            filename = filenames[0].strip() if filenames else 'attachment.bin'
            
            # Encode to base64
            encoded_content = base64.b64encode(attachment_bytes).decode('utf-8')
            
            attachments.append({
                'content': encoded_content,
                'name': filename
            })
        
        # Brevo has a limit on recipients per email
        # We'll send to batches of 50 recipients
        chunk_size = 50
        total_sent = 0
        errors = []
        
        # Split recipients into chunks
        for i in range(0, len(recipients_list), chunk_size):
            chunk = recipients_list[i:i + chunk_size]
            
            payload = {
                'sender': {
                    'name': settings.BREVO_SENDER_NAME,
                    'email': settings.BREVO_SENDER_EMAIL
                },
                'to': chunk,  # Brevo can handle multiple recipients in 'to' field
                'subject': subject,
                'htmlContent': html_content
            }
            
            # Add attachments if present
            if attachments:
                payload['attachment'] = attachments
            
            try:
                response = requests.post(
                    settings.BREVO_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Brevo returns 201 on success
                if response.status_code in [200, 201]:
                    total_sent += len(chunk)
                    print(f"✓ Email batch sent successfully to {len(chunk)} recipients")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', response.text)
                    except:
                        error_msg = response.text
                    
                    error_text = f"Batch error ({response.status_code}): {error_msg}"
                    errors.append(error_text)
                    print(f"✗ {error_text}")
                    
            except Exception as e:
                error_text = f"Request error: {str(e)}"
                errors.append(error_text)
                print(f"✗ {error_text}")
        
        # Determine final result
        if total_sent == len(recipients_list):
            return True, f"Email sent successfully to {total_sent} recipient(s)"
        elif total_sent > 0:
            return True, f"Partially sent to {total_sent}/{len(recipients_list)} recipients. Errors: {'; '.join(errors)}"
        else:
            return False, f"Failed to send emails. Errors: {'; '.join(errors)}"
    
    def _format_html_content(self, title: str, content: str, sender_name: str) -> str:
        """
        Format plain text content into a professional HTML email template.
        Uses the same image hosting approach as account management.
        """
        # Escape HTML to prevent injection
        escaped_content = html.escape(content)
        escaped_title = html.escape(title)
        escaped_sender = html.escape(sender_name)
        
        # Replace newlines with <br> tags
        formatted_content = escaped_content.replace('\n', '<br>')
        
        # Get current year for footer
        from datetime import datetime
        current_year = datetime.now().year
        
        # Use the same public tunnel URL as account management
        PUBLIC_TUNNEL_URL = 'https://rv9qfbq1-8000.asse.devtunnels.ms/'
        logo_url = f"{PUBLIC_TUNNEL_URL}/static/frontend/images/header.png"
        
        # Wrap in professional email template
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .email-header {{
                    background: linear-gradient(135deg, #8B0000 0%, #b71c1c 100%);
                    color: #ffffff;
                    padding: 0;
                    text-align: left;
                    position: relative;
                }}
                .email-header img {{
                    width: 100%;
                    height: auto;
                    display: block;
                }}
                .announcement-badge {{
                    background: rgba(255, 255, 255, 0.95);
                    color: #b71c1c;
                    padding: 12px 24px;
                    font-size: 18px;
                    font-weight: 600;
                    text-align: center;
                    border-bottom: 3px solid #b71c1c;
                }}
                .email-body {{
                    padding: 30px;
                    background: #ffffff;
                }}
                .email-title {{
                    font-size: 22px;
                    font-weight: 600;
                    color: #b71c1c;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #f0f0f0;
                }}
                .email-content {{
                    font-size: 15px;
                    color: #333;
                    margin-bottom: 30px;
                    line-height: 1.8;
                }}
                .email-sender {{
                    padding: 15px;
                    background: #f9f9f9;
                    border-left: 4px solid #b71c1c;
                    margin-top: 20px;
                    font-size: 14px;
                    color: #666;
                }}
                .email-footer {{
                    background: #f9f9f9;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }}
                .email-footer p {{
                    margin: 5px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <img src="{'static/frontend/images/header.png'}" alt="KoopTimizer Header" style="width: 100%; height: auto; display: block;">
                    <div class="announcement-badge">
                        Official Cooperative Announcement
                    </div>
                </div>
                <div class="email-body">
                    <div class="email-title">{escaped_title}</div>
                    <div class="email-content">
                        {formatted_content}
                    </div>
                    <div class="email-sender">
                        <strong>From:</strong> {escaped_sender}<br>
                        <strong>Via:</strong> KoopTimizer Announcement System
                    </div>
                </div>
                <div class="email-footer">
                    <p><strong>KoopTimizer - Cooperative Management System</strong></p>
                    <p>This is an automated announcement. Please do not reply to this email.</p>
                    <p>&copy; {current_year} Lipa City Cooperatives Office. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

#     def __init__(self):
#         self.configuration = sib_api_v3_sdk.Configuration()
#         self.configuration.api_key['api-key'] = settings.BREVO_API_KEY
#         self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
#             sib_api_v3_sdk.ApiClient(self.configuration)
#         )

#     def send_bulk_announcement(self, announcement_id: int, subject: str, content: str) -> Tuple[bool, str]:
#         """
#         Send bulk emails for an announcement to all its recipients.
        
#         Args:
#             announcement_id: The ID of the announcement
#             subject: Email subject (announcement title)
#             content: Email body content (will be converted to HTML)
            
#         Returns:
#             Tuple of (success: bool, message: str)
#         """
#         try:
#             # Get all officer emails for this announcement
#             recipients_list = self._get_announcement_recipients(announcement_id)
            
#             if not recipients_list:
#                 return False, "No valid email recipients found"
            
#             # Format content as HTML
#             html_content = self._format_html_content(content)
            
#             # Send using the existing bulk method
#             return self._send_bulk_email(announcement_id, subject, html_content, recipients_list)
            
#         except Exception as e:
#             return False, f"Error sending bulk email: {str(e)}"
    
#     def _get_announcement_recipients(self, announcement_id: int) -> list:
#         """
#         Retrieve all officer email addresses for a given announcement.
#         Handles both cooperative-level and officer-level recipients.
#         """
#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute("""
#                     SELECT DISTINCT o.email, o.fullname
#                     FROM announcement_officer_recipients aor
#                     JOIN officers o ON aor.officer_id = o.officer_id
#                     WHERE aor.announcement_id = %s AND o.email IS NOT NULL AND o.email != ''
                    
#                     UNION
                    
#                     SELECT DISTINCT o.email, o.fullname
#                     FROM announcement_recipients ar
#                     JOIN officers o ON ar.coop_id = o.coop_id
#                     WHERE ar.announcement_id = %s AND o.email IS NOT NULL AND o.email != ''
#                 """, [announcement_id, announcement_id])
                
#                 recipients = cursor.fetchall()
            
#             # Return list of email addresses
#             return [email for email, fullname in recipients if email]
            
#         except Exception as e:
#             print(f"Error retrieving recipients: {e}")
#             return []
    
#     def _send_bulk_email(self, announcement_id: int, subject: str, html_content: str, recipients_list: list) -> Tuple[bool, str]:
#         """
#         Send email to multiple recipients using BCC.
        
#         Args:
#             announcement_id: ID for tracking
#             subject: Email subject
#             html_content: HTML formatted email body
#             recipients_list: List of email addresses
            
#         Returns:
#             Tuple of (success: bool, message: str)
#         """
#         if not recipients_list:
#             return False, "No valid email recipients found"

#         sender = {
#             "name": settings.DEFAULT_FROM_NAME,
#             "email": settings.DEFAULT_FROM_EMAIL
#         }
        
#         # Brevo BCC limit: 50 recipients per call
#         chunk_size = 45
#         chunks = [recipients_list[i:i + chunk_size] for i in range(0, len(recipients_list), chunk_size)]

#         errors = []
#         success_count = 0

#         for chunk in chunks:
#             # Convert list of strings to list of objects for Brevo
#             bcc_emails = [{"email": email} for email in chunk]
            
#             # Must have at least one "To" address
#             to = [{"email": settings.DEFAULT_FROM_EMAIL, "name": "Announcement Copy"}]

#             send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
#                 to=to,
#                 bcc=bcc_emails,
#                 sender=sender,
#                 subject=subject,
#                 html_content=html_content,
#                 tags=["announcement", f"announcement_{announcement_id}"]
#             )

#             try:
#                 self.api_instance.send_transac_email(send_smtp_email)
#                 success_count += len(chunk)
#             except ApiException as e:
#                 errors.append(f"Batch error: {str(e)}")

#         if errors:
#             if success_count > 0:
#                 return True, f"Partially sent to {success_count} recipients. Errors: {', '.join(errors)}"
#             else:
#                 return False, f"All batches failed: {', '.join(errors)}"
        
#         return True, f"Email sent successfully to {success_count} recipient(s)"
    
#     def _format_html_content(self, text_content: str) -> str:
#         """
#         Convert plain text to professional HTML email format.
#         """
#         # Escape HTML special characters
#         import html
#         escaped_content = html.escape(text_content)
        
#         # Replace newlines with <br> tags
#         html_content = escaped_content.replace('\n', '<br>')
        
#         # Wrap in professional email template
#         return f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="UTF-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <style>
#                 body {{
#                     font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
#                     line-height: 1.6;
#                     color: #333;
#                     background-color: #f4f4f4;
#                     margin: 0;
#                     padding: 0;
#                 }}
#                 .email-container {{
#                     max-width: 600px;
#                     margin: 20px auto;
#                     background: #ffffff;
#                     border-radius: 8px;
#                     overflow: hidden;
#                     box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#                 }}
#                 .email-header {{
#                     background: #b71c1c;
#                     color: #ffffff;
#                     padding: 20px;
#                     text-align: center;
#                 }}
#                 .email-header h1 {{
#                     margin: 0;
#                     font-size: 24px;
#                     font-weight: 600;
#                 }}
#                 .email-body {{
#                     padding: 30px;
#                     background: #ffffff;
#                 }}
#                 .email-content {{
#                     font-size: 15px;
#                     color: #333;
#                     margin-bottom: 20px;
#                 }}
#                 .email-footer {{
#                     background: #f9f9f9;
#                     padding: 20px;
#                     text-align: center;
#                     font-size: 12px;
#                     color: #666;
#                     border-top: 1px solid #e0e0e0;
#                 }}
#                 .email-footer p {{
#                     margin: 5px 0;
#                 }}
#             </style>
#         </head>
#         <body>
#             <div class="email-container">
#                 <div class="email-header">
#                     <h1>Cooperative Announcement</h1>
#                 </div>
#                 <div class="email-body">
#                     <div class="email-content">
#                         {html_content}
#                     </div>
#                 </div>
#                 <div class="email-footer">
#                     <p><strong>Cooperative Management System</strong></p>
#                     <p>This is an automated announcement. Please do not reply to this email.</p>
#                     <p>&copy; {__import__('datetime').datetime.now().year} All rights reserved.</p>
#                 </div>
#             </div>
#         </body>
#         </html>
#         """