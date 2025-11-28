# Push Notification Implementation - Issues Fixed

## Issues Identified

### 1. ❌ **CRITICAL: Duplicate `ready()` method in `apps.py`**
   - **Problem**: Two `ready()` methods were defined, causing the second to overwrite the first
   - **Impact**: Signals were not being imported/activated, and scheduler might not start
   - **Fix**: Merged both methods into a single `ready()` method

### 2. ❌ **CRITICAL: Message model has no `receiver` field**
   - **Problem**: Signal tried to access `instance.receiver` on `Message` model, but `Message` doesn't have a `receiver` field
   - **Impact**: Signal would crash with `AttributeError` when trying to send notifications
   - **Fix**: Changed signal to listen to `MessageRecipient` post_save instead, which has both `message` and `receiver` fields

### 3. ❌ **CRITICAL: Stored procedures bypass Django ORM signals**
   - **Problem**: Messages are created via stored procedure `sp_send_message`, which directly inserts into database, bypassing Django ORM
   - **Impact**: `post_save` signals don't fire for messages created via stored procedures
   - **Fix**: Added manual push notification trigger in `send_message` view after stored procedure calls

### 4. ⚠️ **MINOR: Error handling improvements**
   - **Problem**: Limited error handling and logging
   - **Fix**: Added better error handling, traceback logging, and safe null checks

---

## Files Modified

### 1. `apps/communications/apps.py`
**Changes:**
- Merged duplicate `ready()` methods into one
- Ensures both signals are imported AND scheduler starts

**Before:**
```python
def ready(self):
    # Start scheduler
    ...

def ready(self):  # This overwrites the first one!
    # Import signals
    ...
```

**After:**
```python
def ready(self):
    # Import signals to activate them
    import apps.communications.signals
    
    # Start scheduler in main process
    ...
```

---

### 2. `apps/communications/signals.py`
**Changes:**
- Changed signal from `Message.post_save` to `MessageRecipient.post_save`
- Created reusable helper function `send_push_notification_for_message()`
- Added better error handling and null safety

**Before:**
```python
@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    recipient_user = instance.receiver  # ❌ Message has no receiver field!
    ...
```

**After:**
```python
@receiver(post_save, sender=MessageRecipient)
def send_message_notification(sender, instance, created, **kwargs):
    message = instance.message  # ✅ MessageRecipient has message field
    receiver_user = instance.receiver  # ✅ MessageRecipient has receiver field
    ...
```

---

### 3. `apps/communications/views.py` (send_message function)
**Changes:**
- Added manual push notification trigger after stored procedure calls
- Captures message IDs from stored procedure results
- Calls notification function for each created message

**Added Code:**
```python
# After stored procedure calls, manually trigger notifications
from .signals import send_push_notification_for_message

for message_id in created_message_ids:
    try:
        message = Message.objects.get(message_id=message_id)
        receiver_user = User.objects.get(user_id=receiver_id)
        send_push_notification_for_message(message, receiver_user)
    except Exception as e:
        print(f"Error sending push notification: {e}")
```

---

## How It Works Now

### Flow 1: Message via Stored Procedure (Primary Path)
1. User sends message → `send_message` view called
2. View calls `sp_send_message` stored procedure
3. Stored procedure inserts into `messages` and `message_recipients` tables
4. View captures returned `message_id` from stored procedure
5. View manually calls `send_push_notification_for_message()` 
6. Notification sent to recipient via webpush

### Flow 2: Message via Django ORM (Fallback)
1. Message created via Django ORM (if ever used)
2. `MessageRecipient.post_save` signal fires
3. Signal calls `send_push_notification_for_message()`
4. Notification sent to recipient via webpush

---

## Testing Checklist

- [ ] Send a text message → Should receive push notification
- [ ] Send a file attachment → Should receive push notification
- [ ] Send message to user who hasn't subscribed → Should not crash
- [ ] Check browser console for errors
- [ ] Verify notification appears in browser
- [ ] Click notification → Should navigate to `/communications/message/`

---

## Potential Issues to Watch For

### 1. Webpush User Model Compatibility
- **Issue**: `webpush.send_user_notification()` expects a Django User model
- **Status**: Should work - custom User model has `pk` property
- **If fails**: May need to ensure webpush can find PushSubscription by user ID

### 2. Service Worker Registration
- **Issue**: Service worker must be registered for push notifications to work
- **Check**: Verify `/sw.js` is accessible and registered in browser
- **Location**: `static/service-worker.js` and `templates/sw.js`

### 3. VAPID Keys
- **Issue**: VAPID keys must be configured in settings
- **Check**: `WEBPUSH_SETTINGS` in `settings.py` must have valid keys
- **Location**: `kooptimizer/settings.py` lines 263-267

---

## Debugging Tips

### Check if signals are loaded:
```python
# In Django shell
from django.apps import apps
apps.get_app_config('communications').ready()
```

### Check if notifications are being sent:
- Look for print statements in console: `"Error sending push notification: ..."`
- Check browser console for service worker errors
- Verify PushSubscription exists in database: `webpush_pushsubscription` table

### Test notification manually:
```python
# In Django shell
from webpush import send_user_notification
from apps.users.models import User

user = User.objects.get(user_id=1)
send_user_notification(
    user=user,
    payload={
        "head": "Test",
        "body": "Test notification",
        "icon": "/static/frontend/images/Logo.png",
        "url": "/communications/message/"
    }
)
```

---

## Summary

✅ **Fixed**: Duplicate `ready()` method  
✅ **Fixed**: Signal listening to wrong model  
✅ **Fixed**: Stored procedure bypassing signals  
✅ **Improved**: Error handling and logging  

**Status**: Push notifications should now work for messages sent via stored procedures!

