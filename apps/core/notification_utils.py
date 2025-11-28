"""
Utility functions for sending push notifications.
Provides a centralized way to send notifications to users.
"""
import logging
from webpush import send_user_notification
from django.contrib.auth.models import User as DjangoUser

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body, url="/", icon="/static/frontend/images/Logo.png", ttl=1000):
    """
    Send a push notification to a user.
    
    Args:
        user: Custom User instance (apps.users.models.User)
        title: Notification title/head
        body: Notification body/message
        url: URL to navigate to when notification is clicked (default: "/")
        icon: Icon URL for the notification (default: Logo.png)
        ttl: Time to live in seconds (default: 1000)
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        if not user:
            logger.warning("Cannot send notification: user is None")
            return False
        
        # Truncate body to 50 chars to keep popup clean
        body_preview = body[:50] + "..." if len(body) > 50 else body
        
        payload = {
            "head": title,
            "body": body_preview,
            "icon": icon,
            "url": url
        }
        
        # Map custom User to Django User for webpush
        try:
            django_user = DjangoUser.objects.get(username=user.username)
            
            # Check if user has any push subscriptions
            from webpush.models import PushInformation
            subscription_count = PushInformation.objects.filter(user=django_user).count()
            
            if subscription_count == 0:
                logger.warning(f"User {user.username} has no push subscriptions (Django User exists but not subscribed)")
                return False
            
            # Send the notification
            send_user_notification(user=django_user, payload=payload, ttl=ttl)
            logger.info(f"Push notification sent to {user.username}: {title} ({subscription_count} subscription(s))")
            return True
        except DjangoUser.DoesNotExist:
            # Django User doesn't exist yet - user hasn't subscribed to push
            logger.warning(f"User {user.username} has not subscribed to push notifications (no Django User found)")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification to {user.username}: {e}", exc_info=True)
            return False
                
    except Exception as e:
        logger.error(f"Error sending push notification: {e}", exc_info=True)
        return False


def send_notification_to_cooperative_officers(coop, title, body, url="/", icon="/static/frontend/images/Logo.png"):
    """
    Send push notification to all officers of a cooperative.
    
    Args:
        coop: Cooperatives instance
        title: Notification title
        body: Notification body
        url: URL to navigate to when clicked
        icon: Icon URL
    
    Returns:
        int: Number of notifications sent successfully
    """
    from apps.cooperatives.models import Officer
    from apps.users.models import User as CustomUser
    
    try:
        # Get all officers for this cooperative
        officers = Officer.objects.filter(coop=coop)
        total_officers = officers.count()
        
        logger.info(f"Attempting to send notifications to {total_officers} officer(s) of {coop.cooperative_name}")
        
        if total_officers == 0:
            logger.warning(f"No officers found for cooperative {coop.cooperative_name}")
            return 0
        
        sent_count = 0
        for officer in officers:
            try:
                # Get the user associated with this officer
                user = CustomUser.objects.get(user_id=officer.user_id)
                logger.debug(f"Sending notification to officer: {user.username}")
                
                if send_push_notification(user, title, body, url, icon):
                    sent_count += 1
                    logger.debug(f"Successfully sent notification to {user.username}")
                else:
                    logger.debug(f"Failed to send notification to {user.username} (user may not be subscribed)")
            except CustomUser.DoesNotExist:
                logger.warning(f"Officer {officer.officer_id} has no associated user")
            except Exception as e:
                logger.error(f"Error sending notification to officer {officer.officer_id}: {e}", exc_info=True)
        
        logger.info(f"Sent {sent_count}/{total_officers} notifications to officers of {coop.cooperative_name}")
        return sent_count
        
    except Exception as e:
        logger.error(f"Error sending notifications to cooperative officers: {e}", exc_info=True)
        return 0

