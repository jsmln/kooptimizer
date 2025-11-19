"""
Automatic scheduler for sending scheduled announcements.
This runs in the background as long as the Django server is running.
"""
import threading
import time
from django.utils import timezone
from django.db import connection
from apps.communications.models import Announcement
from apps.core.services.sms_service import SmsService
import logging

logger = logging.getLogger(__name__)


class AnnouncementScheduler:
    """Background scheduler that checks and sends scheduled announcements every minute."""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background scheduler thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Announcement scheduler started")
    
    def stop(self):
        """Stop the background scheduler thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Announcement scheduler stopped")
    
    def _run(self):
        """Main scheduler loop - runs every minute."""
        while self.running:
            try:
                self._check_and_send_scheduled()
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
            
            # Sleep for 60 seconds (check every minute)
            time.sleep(60)
    
    def _check_and_send_scheduled(self):
        """Check for scheduled announcements that are due and send them."""
        try:
            # Close old database connections to avoid "connection already closed" errors
            connection.close()
            
            now = timezone.now()
            
            # Find scheduled announcements that are due
            scheduled_announcements = Announcement.objects.filter(
                status_classification='scheduled',
                sent_at__lte=now
            )
            
            for announcement in scheduled_announcements:
                try:
                    logger.info(f"Processing scheduled announcement: {announcement.title} (ID: {announcement.announcement_id})")
                    
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
                            logger.info(f"✓ Sent SMS announcement: {announcement.title}")
                        else:
                            logger.error(f"✗ Failed to send SMS announcement: {announcement.title} - {message}")
                    
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
                            logger.info(f"✓ Sent Email announcement: {announcement.title}")
                        else:
                            logger.error(f"✗ Failed to send Email announcement: {announcement.title} - {message}")
                
                except Exception as e:
                    logger.error(f"Error processing announcement {announcement.announcement_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error checking scheduled announcements: {str(e)}")


# Global scheduler instance
_scheduler = None


def get_scheduler():
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AnnouncementScheduler()
    return _scheduler


def start_scheduler():
    """Start the announcement scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the announcement scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()
