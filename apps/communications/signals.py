from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, MessageRecipient
from apps.core.notification_utils import send_push_notification

def send_push_notification_for_message(message, receiver_user):
    """
    Helper function to send push notification for a message.
    Can be called from signals or directly from views.
    """
    try:
        # 1. Define the Notification Content
        # We truncate the body to 50 chars to keep the popup clean
        message_preview = message.message[:50] + "..." if len(message.message) > 50 else message.message
        
        # If it's an attachment only message
        if not message_preview and message.attachment:
            message_preview = "Sent an attachment"

        # Get sender fullname safely
        def get_fullname(user_obj):
            if not user_obj:
                return "Unknown"
            # Try Admin profile (OneToOneField, related_name defaults to lowercase model name)
            try:
                if hasattr(user_obj, 'admin'):
                    fullname = getattr(user_obj.admin, 'fullname', None)
                    if fullname:
                        return fullname
            except Exception:
                pass
            
            # Try Staff profile
            try:
                if hasattr(user_obj, 'staff'):
                    fullname = getattr(user_obj.staff, 'fullname', None)
                    if fullname:
                        return fullname
            except Exception:
                pass
            
            # Try Officer profile (uses custom related_name, ForeignKey returns queryset)
            try:
                if hasattr(user_obj, 'cooperatives_officer_profile'):
                    officer = user_obj.cooperatives_officer_profile.first()
                    if officer:
                        fullname = getattr(officer, 'fullname', None)
                        if fullname:
                            return fullname
            except Exception:
                pass
            
            # Fallback to username
            return getattr(user_obj, 'username', 'Unknown')
        
        sender_name = get_fullname(message.sender)

        # Use the centralized notification utility
        return send_push_notification(
            user=receiver_user,
            title=f"New message from {sender_name}",
            body=message_preview,
            url="/communications/message/"
        )
                
    except Exception as e:
        # Log error but don't stop the message from saving
        print(f"Error sending push notification: {e}")
        import traceback
        traceback.print_exc()
        return False

@receiver(post_save, sender=MessageRecipient, dispatch_uid='message_recipient_post_save_notification')
def send_message_notification(sender, instance, created, **kwargs):
    """
    Send push notification when a MessageRecipient is created.
    This works for both ORM and stored procedure inserts (if signals fire).
    """
    # Only trigger notification for NEW message recipients (created=True)
    if created:
        try:
            # Get the message and receiver from the MessageRecipient instance
            message = instance.message
            receiver_user = instance.receiver
            
            # Only send if message and receiver exist
            if message and receiver_user:
                send_push_notification_for_message(message, receiver_user)
                
        except Exception as e:
            # Log error but don't stop the message from saving
            print(f"Error in message notification signal: {e}")
            import traceback
            traceback.print_exc()