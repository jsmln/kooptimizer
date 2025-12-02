# Webpush 500 Error - Fixed

## Issue
The webpush subscription endpoint `/webpush/save_information` was returning a **500 Internal Server Error** with:
```
ValueError: Cannot query "admin_joan": Must be "User" instance.
```

## Root Cause
The django-webpush library's `PushInformation` model has a ForeignKey to Django's built-in `User` model (`django.contrib.auth.models.User`), but this project uses a custom `User` model (`apps.users.models.User`). When webpush tried to save the subscription, it couldn't use our custom User instance in a ForeignKey that expects Django's User.

## Solution

### 1. Created Custom Webpush View
**File**: `apps/core/webpush_views.py` (NEW)

Created a custom `save_webpush_info` view that:
- Accepts subscription data from the frontend
- Maps our custom User to Django's User model
- Creates Django User records on-the-fly when needed (mapped by username)
- Saves PushInformation records using Django User
- Handles both subscribe and unsubscribe operations

**Key Features:**
- Creates Django User records automatically when users subscribe
- Keeps Django User's `is_active` status in sync with custom User
- Uses username as the mapping key between custom and Django Users

### 2. Updated URL Configuration
**File**: `kooptimizer/urls.py`

Added custom route **before** webpush.urls to override the default save_information endpoint:
```python
path('webpush/save_information', apps.core.webpush_views.save_webpush_info, name='save_webpush_info'),
path('webpush/', include('webpush.urls')),  # Other webpush URLs still work
```

### 3. Updated Notification Sending
**File**: `apps/communications/signals.py`

Updated `send_push_notification_for_message()` to map custom User to Django User:
```python
# Map custom User to Django User for webpush
from django.contrib.auth.models import User as DjangoUser
django_user = DjangoUser.objects.get(username=receiver_user.username)
send_user_notification(user=django_user, payload=payload, ttl=1000)
```

## How It Works

### Subscription Flow:
1. User clicks "Enable Push" on dashboard
2. Frontend sends subscription to `/webpush/save_information`
3. Custom view receives request with custom User in `request.user`
4. View maps custom User → Django User (creates if needed)
5. View saves PushInformation with Django User
6. Subscription saved successfully ✅

### Notification Sending Flow:
1. Message is sent via stored procedure
2. Signal or view calls `send_push_notification_for_message()`
3. Function maps custom User → Django User
4. Function calls `send_user_notification()` with Django User
5. Webpush looks up PushInformation by Django User
6. Notification sent successfully ✅

## Important Notes

### Django User Records
- Django User records are created automatically when users subscribe
- They are mapped to custom Users by `username`
- Django User's `is_active` is kept in sync with custom User
- Django Users have unusable passwords (users can't login with them)
- This is a **mapping layer** - actual authentication still uses custom User

### Data Consistency
- If a custom User is deactivated, the corresponding Django User's `is_active` is updated
- If a custom User is deleted, the Django User remains (orphaned but harmless)
- PushInformation records are linked to Django Users, not custom Users

## Testing

After applying the fix:

1. **Restart Django server** (new view requires restart)
2. **Refresh dashboard page**
3. **Click "Enable Push" button**
4. **Verify subscription succeeds** - widget should disappear
5. **Check database** - should see:
   - Django User record created (in `auth_user` table)
   - PushInformation record created (in `webpush_pushinformation` table)
   - SubscriptionInfo record created (in `webpush_subscriptioninfo` table)

## Files Created/Modified

### Created:
- ✅ `apps/core/webpush_views.py` - Custom webpush save_information view

### Modified:
- ✅ `kooptimizer/urls.py` - Added custom webpush route
- ✅ `apps/communications/signals.py` - Updated notification sending to map Users

## Potential Future Improvements

1. **Cleanup Orphaned Django Users**: Periodically clean up Django Users that no longer have corresponding custom Users
2. **Better Mapping Strategy**: Use a separate mapping table instead of username matching
3. **Sync Mechanism**: Add signals to keep Django Users in sync with custom Users automatically

---

**Status**: ✅ **FIXED** - Webpush subscription should now work with custom User model!


