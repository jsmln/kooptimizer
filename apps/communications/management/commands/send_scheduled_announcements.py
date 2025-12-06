"""
Management command to send scheduled announcements.
Run this command periodically (e.g., every minute via cron job or task scheduler).

Usage:
    python manage.py send_scheduled_announcements
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from apps.communications.models import Announcement
from apps.core.services.sms_service import SmsService


class Command(BaseCommand):
    help = 'Sends scheduled announcements that are due'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find scheduled announcements that are due
        scheduled_announcements = Announcement.objects.filter(
            status_classification='scheduled',
            sent_at__lte=now
        )
        
        sent_count = 0
        error_count = 0
        
        for announcement in scheduled_announcements:
            try:
                self.stdout.write(f"Processing announcement: {announcement.title} (ID: {announcement.announcement_id})")
                
                # Send based on type
                if announcement.type == 'sms':
                    sms_service = SmsService()
                    success, message = sms_service.send_bulk_announcement(
                        announcement.announcement_id,
                        announcement.description
                    )
                    
                    if success:
                        # Update status to sent
                        announcement.status_classification = 'sent'
                        announcement.save()
                        sent_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Sent SMS announcement: {announcement.title}"
                            )
                        )
                    else:
                        error_count += 1
                        # Show user-friendly message in command output
                        user_msg = "SMS service temporarily unavailable. Contact support for assistance."
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Failed to send SMS announcement: {announcement.title} - {user_msg}"
                            )
                        )
                        # Log technical details for debugging
                        self.stdout.write(
                            self.style.WARNING(
                                f"   Technical details: {message}"
                            )
                        )
                        
                elif announcement.type == 'e-mail':
                    from apps.core.services.email_service import EmailService
                    email_service = EmailService()
                    success, message = email_service.send_bulk_announcement(
                        announcement.announcement_id,
                        announcement.description
                    )
                    
                    if success:
                        # Update status to sent
                        announcement.status_classification = 'sent'
                        announcement.save()
                        sent_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Sent Email announcement: {announcement.title}"
                            )
                        )
                    else:
                        error_count += 1
                        # Show user-friendly message in command output
                        user_msg = "Email service temporarily unavailable. Contact support for assistance."
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Failed to send Email announcement: {announcement.title} - {user_msg}"
                            )
                        )
                        # Log technical details for debugging
                        self.stdout.write(
                            self.style.WARNING(
                                f"   Technical details: {message}"
                            )
                        )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error processing announcement {announcement.announcement_id}: {str(e)}"
                    )
                )
        
        # Summary
        if sent_count > 0 or error_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n=== Summary ===\nSent: {sent_count}\nErrors: {error_count}"
                )
            )
        else:
            self.stdout.write("No scheduled announcements due at this time.")
