# Push Notification Troubleshooting Guide

## Issue: Push Notifications Not Working

### Diagnosis Results

The notification system is **working correctly**, but notifications aren't being received because:

1. ✅ **Signals are firing** - Profile save signals are working
2. ✅ **Notification system works** - Test notifications can be sent
3. ❌ **Users haven't subscribed** - Most officers haven't enabled push notifications in their browsers

### How to Enable Push Notifications

1. **Go to your Dashboard**
   - Navigate to `/dashboard/` in your browser
   - Look for the "Enable Push Notifications" button

2. **Click "Enable Push Notifications"**
   - Your browser will ask for permission
   - Click "Allow" when prompted

3. **Verify Subscription**
   - After clicking, you should see "Push Notifications Enabled"
   - Check browser console (F12) for any errors

4. **Test Notification**
   - Run: `python test_push_notifications.py`
   - You should receive a test notification

### Common Issues

#### 1. Browser Blocking Notifications
- **Chrome/Edge**: Check site settings → Notifications → Allow
- **Firefox**: Check site permissions → Notifications → Allow
- **Safari**: Safari doesn't support web push notifications

#### 2. Service Worker Not Registered
- Open DevTools (F12) → Application → Service Workers
- Check if `/sw.js` is registered
- If not, refresh the page and try again

#### 3. HTTPS Required
- Push notifications require HTTPS (or localhost)
- If using `http://127.0.0.1:8000`, it should work
- If using a domain, ensure HTTPS is enabled

#### 4. VAPID Keys Not Configured
- Check `settings.py` for `WEBPUSH_SETTINGS`
- Ensure VAPID keys are set correctly

### Testing

1. **Test if you're subscribed:**
   ```bash
   python test_push_notifications.py
   ```

2. **Test profile notification:**
   ```bash
   python test_profile_notification.py
   ```

3. **Check server logs:**
   - Look for: `"Sent X notifications to officers"`
   - If you see `"Sent 0/X"`, users haven't subscribed

### For Profile Update Notifications

When you create or update a profile:
1. Signal fires automatically ✅
2. System finds all officers of the cooperative ✅
3. Sends notification to each officer who has subscribed ✅
4. If no officers are subscribed, 0 notifications are sent

**Solution**: All officers need to enable push notifications in their browsers.

### Manual Test

To manually test if notifications work for you:

```python
# In Django shell: python manage.py shell
from apps.users.models import User
from apps.core.notification_utils import send_push_notification

user = User.objects.get(username='your_username')
send_push_notification(
    user=user,
    title="Test Notification",
    body="This is a test",
    url="/dashboard/"
)
```

If this works, the system is fine - you just need to ensure all users have subscribed.

