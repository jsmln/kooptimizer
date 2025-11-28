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
        data = json.loads(request.body)
        status_type = data.get('status_type')
        subscription_data = data.get('subscription')
        group_name = data.get('group', None)
        
        # Check authentication
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Get custom user
        custom_user = request.user
        if not isinstance(custom_user, CustomUser):
            return JsonResponse({'error': 'Invalid user type'}, status=400)
        
        # Get or create subscription info
        subscription_info, _ = SubscriptionInfo.objects.get_or_create(
            endpoint=subscription_data.get('endpoint'),
            defaults={
                'keys': subscription_data.get('keys', {}),
            }
        )
        
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
            django_user, created = DjangoUser.objects.get_or_create(
                username=custom_user.username,
                defaults={
                    'email': getattr(custom_user, 'email', f'{custom_user.username}@kooptimizer.local'),
                    'is_active': custom_user.is_active,
                    'password': '!',  # Set unusable password (user won't login with this)
                }
            )
            
            # Update Django User to match custom user's active status
            if django_user.is_active != custom_user.is_active:
                django_user.is_active = custom_user.is_active
                django_user.save()
            
            # Now create PushInformation with Django User
            # Note: PushInformation model only has: user, subscription, group fields
            push_info, created = PushInformation.objects.get_or_create(
                user=django_user,
                subscription=subscription_info,
                group=group
            )
            
            if created:
                logger.info(f"User {custom_user.username} subscribed to push notifications")
            else:
                logger.debug(f"User {custom_user.username} already subscribed to push notifications")
            
            return JsonResponse({'status': 'subscribed'}, status=201)
            
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

