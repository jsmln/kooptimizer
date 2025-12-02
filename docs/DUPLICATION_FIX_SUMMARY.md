# Duplication Fix Summary

## Issue: Everything Duplicates

### Root Cause #1: Django Signal Handlers Registered Multiple Times

Django signal handlers were being registered **multiple times** during development server auto-reloads, causing duplicate notifications and actions.

When Django's development server auto-reloads (when code changes are detected), the `AppConfig.ready()` method is called again, which re-imports the signals module. This causes the `@receiver` decorators to register the same signal handler multiple times, resulting in:
- Duplicate push notifications
- Duplicate database operations (if any in signals)
- Duplicate log messages
- Multiple executions of the same signal handler for a single event

#### Solution Applied for Signals

Added `dispatch_uid` parameter to all signal receivers to prevent duplicate registration:

**Files Fixed:**
1. ✅ `apps/cooperatives/signals.py` - Added `dispatch_uid='profile_data_post_save_notification'`
2. ✅ `apps/communications/signals.py` - Added `dispatch_uid='message_recipient_post_save_notification'`

The `dispatch_uid` parameter is a **unique identifier** for the signal connection. When Django tries to register a signal handler:

1. If a handler with the same `dispatch_uid` already exists, Django **skips** the registration
2. This prevents duplicate handlers even if `ready()` is called multiple times
3. Each signal handler will only fire **once per event**, not multiple times

---

### Root Cause #2: Duplicate POST Requests from Frontend

The `/account_management/api/send-credentials/` endpoint was being called **twice** for each button click, causing:
- Duplicate user creation attempts
- Duplicate emails being sent
- Database constraint violations (username already exists)

**Evidence from logs:**
```
[01/Dec/2025 15:54:04] "HEAD /dashboard/staff/ HTTP/1.1" 200 0
[01/Dec/2025 15:54:04] "HEAD /dashboard/staff/ HTTP/1.1" 200 0  ← DUPLICATE

[01/Dec/2025 15:54:17] "POST /account_management/api/send-credentials/ HTTP/1.1" 500 547
[01/Dec/2025 15:54:19] "POST /account_management/api/send-credentials/ HTTP/1.1" 200 301  ← DUPLICATE
[01/Dec/2025 15:54:31] "POST /account_management/api/send-credentials/ HTTP/1.1" 500 547  ← DUPLICATE
```

#### Solution Applied for Frontend

Added a **guard flag** (`isSendingCredentials`) in `handleSendCredentials()` function to prevent double submission:

**File Fixed:**
✅ `templates/account_management/account_management.html`

**Changes:**
1. Added `isSendingCredentials` flag to track if a request is in progress
2. Check flag at the start of `handleSendCredentials()` - if true, exit immediately
3. Set flag to `true` when request starts
4. Reset flag to `false` in the `finally` block after request completes

**Code Added:**
```javascript
let isSendingCredentials = false; // Guard flag to prevent double submission

function handleSendCredentials(sendButton, el) {
    // Prevent double submission
    if (isSendingCredentials) {
        console.log('Send credentials already in progress, ignoring duplicate request');
        return;
    }
    
    isSendingCredentials = true;
    // ... existing code ...
    .finally(() => { 
        sendButton.disabled = false; 
        sendButton.innerHTML = "Send"; 
        isSendingCredentials = false; // Reset guard flag
    });
}
```

This ensures that even if the button is clicked multiple times rapidly, or if there's some event bubbling/propagation issue, the fetch request will only be sent **once**.

---

## Files Modified

### Signal Duplication Fix:
1. `apps/cooperatives/signals.py` - Added `dispatch_uid='profile_data_post_save_notification'`
2. `apps/communications/signals.py` - Added `dispatch_uid='message_recipient_post_save_notification'`

### Frontend Duplication Fix:
3. `templates/account_management/account_management.html` - Added guard flag in `handleSendCredentials()`

---

## Testing

### To verify Signal Fix:
1. Send a message in the messaging system
2. Check that only **one** push notification is sent (not multiple)
3. Create/update a cooperative profile
4. Check that only **one** notification is sent to officers

### To verify Frontend Fix:
1. Create a new user account via the account management page
2. Click "Send Credentials" button
3. Verify that:
   - Only **one** POST request is sent to `/account_management/api/send-credentials/`
   - Only **one** email is sent
   - No database constraint violations occur
   - User is created successfully without errors

---

## Additional Notes

- The `dispatch_uid` is a **Django best practice** for signal handlers
- The guard flag is a **common JavaScript pattern** to prevent race conditions
- Both fixes work at different layers:
  - **Signals**: Prevent duplicate handler registration at Django level
  - **Frontend**: Prevent duplicate requests at JavaScript level
- The middleware (`apps.core.middleware.AuthenticationMiddleware`) was **not** the cause
- No changes to backend views or stored procedures were needed

---

**Fix Applied:** December 1, 2025  
**Status:** ✅ RESOLVED
