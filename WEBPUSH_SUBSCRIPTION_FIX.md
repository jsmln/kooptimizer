# Webpush Subscription 400 Error - Fixed

## Issue
The webpush subscription endpoint was returning errors:
1. Initially: **400 Bad Request** error
2. After first fix: **404 Not Found** error (wrong URL pattern)

Both issues have been resolved.

## Root Causes Identified

### 1. ❌ **CSRF Token Not Properly Retrieved**
   - **Problem**: Code was using `'{{ csrf_token }}'` which is a Django template variable that doesn't work in JavaScript
   - **Impact**: CSRF validation failed, causing 400 error

### 2. ❌ **Missing Credentials in Fetch Request**
   - **Problem**: `credentials: 'include'` was missing
   - **Impact**: Cookies (including session cookie) weren't sent, so user authentication failed

### 3. ❌ **Wrong URL Pattern (404 Error)**
   - **Problem**: URL was `/webpush/save_information/` (with trailing slash) but django-webpush uses `/webpush/save_information` (without trailing slash)
   - **Impact**: Django couldn't find the endpoint, causing 404 error

### 4. ❌ **Incorrect Browser Field Format**
   - **Problem**: Sending full `navigator.userAgent` instead of browser name
   - **Impact**: Webpush library expects a browser name (e.g., "chrome", "firefox"), not full user agent string

### 5. ❌ **Missing `user_agent` Field**
   - **Problem**: Webpush library expects both `browser` (name) and `user_agent` (full string)
   - **Impact**: Missing required field

---

## Fixes Applied

### File: `templates/dashboard/dashboard.html`

**Changes Made:**

1. **Added `getCsrfToken()` function** to retrieve CSRF token from cookies:
```javascript
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

2. **Fixed CSRF token retrieval**:
```javascript
// Before:
'X-CSRFToken': '{{ csrf_token }}',  // ❌ Doesn't work

// After:
const csrfToken = getCsrfToken();
if (!csrfToken) {
    throw new Error('CSRF token not found. Please refresh the page and try again.');
}
'X-CSRFToken': csrfToken,  // ✅ Works
```

3. **Added `credentials: 'include'`**:
```javascript
const response = await fetch('/webpush/save_information/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
    },
    credentials: 'include',  // ✅ Added: Sends cookies for authentication
    body: JSON.stringify({...})
});
```

4. **Fixed URL pattern (removed trailing slash)**:
```javascript
// Before:
'/webpush/save_information/'  // ❌ 404 Not Found

// After:
'/webpush/save_information'  // ✅ Correct django-webpush pattern
```

5. **Fixed browser detection**:
```javascript
// Before:
browser: navigator.userAgent  // ❌ Full user agent string

// After:
const browserMatch = navigator.userAgent.match(/(firefox|msie|chrome|safari|trident|edg)/i);
const browser = browserMatch ? browserMatch[0].toLowerCase() : 'chrome';
// ✅ Extracts browser name
```

6. **Added `user_agent` field**:
```javascript
body: JSON.stringify({
    status_type: 'subscribe',
    subscription: subscription.toJSON(),
    browser: browser,           // ✅ Browser name
    user_agent: navigator.userAgent  // ✅ Full user agent
})
```

7. **Improved error handling**:
```javascript
if (response.ok) {
    // Success
} else {
    const errorText = await response.text();  // ✅ Get error details
    console.error("Server Error:", response.status, errorText);
    alert("Server rejected the subscription. Error: " + response.status + "\n" + errorText);
}
```

---

## Testing

After applying the fix:

1. **Refresh the dashboard page** (to get fresh CSRF token in cookies)
2. **Click "Enable Push" button**
3. **Check browser console** for any errors
4. **Verify subscription succeeds** - widget should disappear and show success message

---

## Expected Behavior

✅ **Success Flow:**
1. User clicks "Enable Push"
2. Service worker registers
3. Browser requests notification permission
4. Subscription created
5. Request sent to `/webpush/save_information` with:
   - Valid CSRF token
   - User session cookie (via `credentials: 'include'`)
   - Correct data format
6. Server saves subscription to database
7. Widget disappears, success message shown

❌ **If Still Failing:**
- Check browser console for specific error
- Verify user is logged in (session cookie exists)
- Verify VAPID keys are configured in `.env`
- Check Django server logs for detailed error

---

## Additional Notes

### CSRF Token Source
Django automatically sets a `csrftoken` cookie when:
- User visits any page with `{% csrf_token %}` tag, OR
- User makes any authenticated request

The cookie is available in JavaScript via `document.cookie`.

### Authentication Requirement
The webpush library's `save_information` endpoint requires:
- User to be authenticated (logged in)
- Valid session cookie
- CSRF token

This is why `credentials: 'include'` is critical - it ensures the session cookie is sent with the request.

---

## Files Modified

- ✅ `templates/dashboard/dashboard.html` - Fixed webpush subscription code

---

**Status**: ✅ **FIXED** - Webpush subscription should now work correctly!

