"""
Custom webpush views to work with custom User model.
This overrides the default webpush save_information view to handle custom authentication.
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from webpush.models import PushInformation, SubscriptionInfo, Group
from apps.users.models import User as CustomUser

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def save_webpush_info(request):
    """
    Custom view to save webpush subscription information.
    Works with custom User model instead of Django's built-in User.
    """
    try:
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webpush subscription request: {e}")
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        status_type = data.get('status_type')
        subscription_data = data.get('subscription')
        group_name = data.get('group', None)
        
        # Validate status_type
        if not status_type:
            logger.error("Missing status_type in webpush request")
            return JsonResponse({'error': 'Status type is required'}, status=400)
        
        if status_type not in ['subscribe', 'unsubscribe']:
            logger.error(f"Invalid status_type: {status_type}")
            return JsonResponse({'error': 'Invalid status type. Must be "subscribe" or "unsubscribe"'}, status=400)
        
        # Validate subscription data
        if not subscription_data:
            logger.error("Missing subscription data in webpush request")
            return JsonResponse({'error': 'Subscription data is required'}, status=400)
        
        if not isinstance(subscription_data, dict):
            logger.error(f"Subscription data is not a dict: {type(subscription_data)}")
            return JsonResponse({'error': 'Subscription data must be a valid object'}, status=400)
        
        endpoint = subscription_data.get('endpoint')
        if not endpoint:
            logger.error("Missing endpoint in subscription data")
            return JsonResponse({'error': 'Subscription endpoint is required'}, status=400)
        
        # Extract keys from subscription data
        # SubscriptionInfo model has separate fields: auth and p256dh (not a 'keys' dict)
        keys = subscription_data.get('keys', {})
        if not isinstance(keys, dict):
            keys = {}
        auth_key = keys.get('auth', '') if keys else ''
        p256dh_key = keys.get('p256dh', '') if keys else ''
        
        # Validate that we have the required keys
        if not auth_key or not p256dh_key:
            logger.error(f"Missing auth or p256dh keys in subscription data. Keys: {keys}")
            return JsonResponse({'error': 'Subscription keys (auth and p256dh) are required'}, status=400)
        
        # Check authentication - use session user_id instead of is_authenticated
        # This works better for newly created accounts
        user_id = request.session.get('user_id')
        if not user_id:
            logger.warning("Webpush subscription attempt without user_id in session")
            return JsonResponse({'error': 'Authentication required. Please log in again.'}, status=401)
        
        # Get custom user from session user_id
        try:
            # Handle both string and int user_id
            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                except ValueError:
                    # Try username lookup if it's not a number
                    custom_user = CustomUser.objects.get(username=user_id)
                else:
                    custom_user = CustomUser.objects.get(user_id=user_id)
            else:
                custom_user = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            logger.error(f"User not found for user_id: {user_id}")
            return JsonResponse({'error': 'User not found. Please log in again.'}, status=404)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user_id format: {user_id}, error: {e}")
            return JsonResponse({'error': 'Invalid user session. Please log in again.'}, status=400)
        
        # Get or create subscription info
        # SubscriptionInfo model fields: endpoint, auth, p256dh, browser, user_agent
        try:
            subscription_info, created = SubscriptionInfo.objects.get_or_create(
                endpoint=endpoint,
                defaults={
                    'auth': auth_key,
                    'p256dh': p256dh_key,
                    'browser': data.get('browser', ''),
                    'user_agent': data.get('user_agent', ''),
                }
            )
            # Update existing subscription if keys changed
            if not created:
                updated = False
                if subscription_info.auth != auth_key:
                    subscription_info.auth = auth_key
                    updated = True
                if subscription_info.p256dh != p256dh_key:
                    subscription_info.p256dh = p256dh_key
                    updated = True
                if updated:
                    subscription_info.save()
                    logger.debug(f"Updated SubscriptionInfo keys for endpoint: {endpoint[:50]}...")
            
            if created:
                logger.info(f"Created new SubscriptionInfo for endpoint: {endpoint[:50]}...")
            else:
                logger.debug(f"Using existing SubscriptionInfo for endpoint: {endpoint[:50]}...")
        except Exception as e:
            logger.error(f"Error creating SubscriptionInfo: {e}", exc_info=True)
            return JsonResponse({'error': f'Failed to save subscription information: {str(e)}'}, status=500)
        
        # Get or create group if provided
        group = None
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
        
        # Handle subscribe/unsubscribe
        if status_type == 'subscribe':
            # Create PushInformation record
            # We need to map custom user to Django's User model
            # Since webpush expects django.contrib.auth.models.User,
            # we'll use the user_id as a workaround by creating a temporary mapping
            # or we can modify the approach
            
            # Actually, the issue is that PushInformation has a ForeignKey to User
            # We need to either:
            # 1. Create a Django User for each custom User (not ideal)
            # 2. Modify webpush to work with custom User (complex)
            # 3. Store user_id separately and handle lookups manually
            
            # Map custom User to Django User for webpush compatibility
            # Webpush's PushInformation model requires django.contrib.auth.models.User
            from django.contrib.auth.models import User as DjangoUser
            
            # Get or create a Django User that corresponds to our custom user
            # We use username as the mapping key
            try:
                django_user = None
                try:
                    django_user = DjangoUser.objects.get(username=custom_user.username)
                    # Update existing Django User to match custom user's active status
                    if django_user.is_active != getattr(custom_user, 'is_active', True):
                        django_user.is_active = getattr(custom_user, 'is_active', True)
                        django_user.save()
                except DjangoUser.DoesNotExist:
                    # Create new Django User with unusable password
                    email = getattr(custom_user, 'email', '') or f'{custom_user.username}@kooptimizer.local'
                    django_user = DjangoUser(
                        username=custom_user.username,
                        email=email,
                        is_active=getattr(custom_user, 'is_active', True)
                    )
                    django_user.set_unusable_password()  # Set unusable password before saving
                    django_user.save()
                    logger.info(f"Created Django User mapping for {custom_user.username}")
                    
            except Exception as e:
                logger.error(f"Error creating/getting Django User for {custom_user.username}: {e}", exc_info=True)
                return JsonResponse({'error': f'Failed to set up user account for notifications: {str(e)}'}, status=500)
            
            # Now create PushInformation with Django User
            # Note: PushInformation model only has: user, subscription, group fields
            try:
                push_info, created = PushInformation.objects.get_or_create(
                    user=django_user,
                    subscription=subscription_info,
                    group=group
                )
                
                if created:
                    logger.info(f"User {custom_user.username} (user_id: {custom_user.user_id}) subscribed to push notifications")
                else:
                    logger.debug(f"User {custom_user.username} already subscribed to push notifications")
                
                return JsonResponse({'status': 'subscribed', 'message': 'Push notifications enabled successfully'}, status=201)
            except Exception as e:
                logger.error(f"Error creating PushInformation for user {custom_user.username}: {e}", exc_info=True)
                return JsonResponse({'error': 'Failed to save push notification subscription'}, status=500)
            
        elif status_type == 'unsubscribe':
            # Delete PushInformation
            from django.contrib.auth.models import User as DjangoUser
            try:
                django_user = DjangoUser.objects.get(username=custom_user.username)
                deleted_count = PushInformation.objects.filter(
                    user=django_user,
                    subscription=subscription_info
                ).delete()[0]
                if deleted_count > 0:
                    logger.info(f"User {custom_user.username} unsubscribed from push notifications")
                return JsonResponse({'status': 'unsubscribed'}, status=200)
            except DjangoUser.DoesNotExist:
                logger.debug(f"User {custom_user.username} was not subscribed (Django User not found)")
                return JsonResponse({'status': 'unsubscribed'}, status=200)
        else:
            return JsonResponse({'error': 'Invalid status_type'}, status=400)
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webpush subscription request")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in save_webpush_info: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

