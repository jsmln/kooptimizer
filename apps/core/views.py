from django.shortcuts import render
from django.core.cache import cache


def download_view(request):
    # We don't have a download.html, so just render the home for now
    return render(request, 'download.html') 

def about_view(request):
    # Render the about page
    return render(request, 'about.html')

def access_denied_view(request):
    """
    Shows access denied page for unauthenticated users
    """
    import time
    now = int(time.time())
    
    # Check for account-based lockout in cache (works across all browsers)
    locked_out_username = request.session.get('locked_out_username')
    is_locked_out = False
    lockout_until = None
    
    if locked_out_username:
        # Normalize username to lowercase for consistent cache key lookup
        username_normalized = locked_out_username.lower() if isinstance(locked_out_username, str) else str(locked_out_username).lower()
        lockout_cache_key = f'login_lockout_{username_normalized}'
        lockout_until = cache.get(lockout_cache_key)
        is_locked_out = lockout_until and now < lockout_until
        
        # If lockout expired, clear the session variable
        if not is_locked_out:
            request.session.pop('locked_out_username', None)
    
    context = {
        'now': now,
        'lockout_until': lockout_until if is_locked_out else None,
        'is_locked_out': is_locked_out
    }
    return render(request, 'access_denied.html', context, status=403)



