"""
Signals for cooperative-related models.
Sends push notifications for profile updates and yearly reminders.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
import logging
from .models import ProfileData
from apps.core.notification_utils import send_notification_to_cooperative_officers

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProfileData, dispatch_uid='profile_data_post_save_notification')
def send_profile_update_notification(sender, instance, created, **kwargs):
    """
    Send push notification when a profile is created or updated.
    Only sends for current year profiles to avoid spam.
    """
    try:
        logger.info(f"ProfileData post_save signal fired: created={created}, profile_id={instance.profile_id}, report_year={instance.report_year}")
        
        current_year = date.today().year
        
        # Only send notifications for current year profiles
        if instance.report_year != current_year:
            logger.debug(f"Skipping notification for profile year {instance.report_year} (current year is {current_year})")
            return
        
        # Get the cooperative
        coop = instance.coop
        if not coop:
            logger.warning(f"Profile {instance.profile_id} has no cooperative associated")
            return
        
        logger.info(f"Sending notification for cooperative: {coop.cooperative_name}")
        
        if created:
            # New profile created
            title = "Profile Created Successfully"
            body = f"Your cooperative profile for {instance.report_year} has been created and is pending approval."
            url = f"/cooperatives/profile_form/"
        else:
            # Profile updated
            title = "Profile Updated"
            body = f"Your cooperative profile for {instance.report_year} has been updated."
            url = f"/cooperatives/profile_form/"
        
        # Send notification to all officers
        sent_count = send_notification_to_cooperative_officers(
            coop=coop,
            title=title,
            body=body,
            url=url
        )
        
        logger.info(f"Profile notification sent to {sent_count} officer(s)")
        
    except Exception as e:
        logger.error(f"Error sending profile update notification: {e}", exc_info=True)


def check_and_notify_yearly_profile_updates():
    """
    Check for cooperatives that need to update their profile for the new year.
    This should be called by a scheduled task (e.g., daily or weekly).
    """
    try:
        from apps.account_management.models import Cooperatives
        from apps.cooperatives.models import ProfileData
        
        current_year = date.today().year
        previous_year = current_year - 1
        
        # Find all active cooperatives
        cooperatives = Cooperatives.objects.all()
        
        notified_count = 0
        for coop in cooperatives:
            try:
                # Check if they have a profile for the current year
                current_profile = ProfileData.objects.filter(
                    coop=coop,
                    report_year=current_year
                ).first()
                
                # If they don't have a current year profile, but have a previous year profile
                if not current_profile:
                    previous_profile = ProfileData.objects.filter(
                        coop=coop,
                        report_year=previous_year
                    ).first()
                    
                    if previous_profile:
                        # Send reminder notification
                        title = "Yearly Profile Update Required"
                        body = f"Please update your cooperative profile for {current_year}. Your {previous_year} profile is on file."
                        url = "/cooperatives/profile_form/"
                        
                        sent = send_notification_to_cooperative_officers(
                            coop=coop,
                            title=title,
                            body=body,
                            url=url
                        )
                        
                        if sent > 0:
                            notified_count += 1
                            logger.info(f"Sent yearly update reminder to {coop.cooperative_name}")
            
            except Exception as e:
                logger.error(f"Error checking profile for {coop.cooperative_name}: {e}")
        
        logger.info(f"Yearly profile update check completed. Notified {notified_count} cooperatives.")
        return notified_count
        
    except Exception as e:
        logger.error(f"Error in yearly profile update check: {e}", exc_info=True)
        return 0

