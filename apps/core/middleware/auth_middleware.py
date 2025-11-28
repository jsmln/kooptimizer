from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import resolve
from django.http import HttpResponseRedirect, JsonResponse
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

class AuthenticationMiddleware:
    """
    Middleware to ensure users are authenticated before accessing protected pages.
    Shows access denied page for unauthenticated users.
    Prevents manual URL typing by keeping users on their current page.
    Checks strictly for Account Deactivation status.
    """
    
    # URLs that don't require authentication
    PUBLIC_URLS = [
        'home',           # Home page
        'login',          # Login page
        'about',          # About page
        'download',       # Download page
        'users:logout',   # Logout (to clear session)
        'access_denied',  # Access denied page
        'users:initiate_password_reset', # Allow searching for account
        'users:perform_password_reset',
        'users:all_events',
        'users:add_event',
    ]
    
    # URLs that require pending verification (not full authentication)
    PENDING_VERIFICATION_URLS = [
        'users:first_login_setup',  # First-time account setup
    ]
    
    # URL prefixes that don't require authentication
    PUBLIC_PREFIXES = [
        '/static/',       # Static files
        '/admin/',        # Django admin (has its own auth)
    ]
    
    # API endpoints that should return 403 JSON instead of redirecting
    API_PREFIXES = [
        '/api/',
        '/communications/api/',
        '/account_management/api/',
        '/cooperatives/api/',
        '/databank/api/',
    ]
    
    # File/attachment endpoints that should always stream files (never redirect)
    FILE_ENDPOINTS = [
        '/communications/api/message/attachment/',
        '/communications/api/announcement/',
        '/databank/api/file/',
    ]
    
    # Conversion endpoints that should always process (never redirect)
    CONVERSION_ENDPOINTS = [
        '/communications/api/message/attachment/',
        '/communications/api/announcement/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check session validity and freshness
        user_id = request.session.get('user_id')
        
        if '/users/all_events/' in request.path or '/users/add_event/' in request.path:
            return self.get_response(request)

        # ---------------------------------------------------------
        # 1. SESSION FRESHNESS CHECK
        # ---------------------------------------------------------
        if request.session.session_key and user_id:
            # Check if session has last_activity timestamp
            last_activity = request.session.get('last_activity')
            current_time = __import__('time').time()
            
            # Validate session freshness
            if last_activity:
                from django.conf import settings
                session_age = getattr(settings, 'SESSION_COOKIE_AGE', 900) #15 minutes
                
                if (current_time - last_activity) > session_age:
                    # Session expired due to inactivity - clear it
                    request.session.flush()
                    if request.path_info not in ['/login/', '/', '/about/', '/download/']:
                        messages.warning(request, 'Your session has expired due to inactivity. Please log in again.')
                        return redirect('login')
            else:
                # No last_activity means this is a stale/restored session
                request.session.flush()
                if request.path_info not in ['/login/', '/', '/about/', '/download/']:
                    messages.warning(request, 'Your session has expired. Please log in again.')
                    return redirect('login')
            
            # Update last activity timestamp
            request.session['last_activity'] = current_time

            # ---------------------------------------------------------
            # 2. ACCOUNT STATUS CHECK (NEW LOGIC)
            # ---------------------------------------------------------
            try:
                UserModel = apps.get_model('users', 'Users') 
                user = UserModel.objects.get(pk=user_id)

                if not user.is_active: 
                    request.session.flush()
                    messages.error(request, 'Your account has been deactivated. Access denied.')
                    return redirect('access_denied')
            
            except (LookupError, ImportError):
                pass
                
            except ObjectDoesNotExist: 
                request.session.flush()
                return redirect('login')

        # ---------------------------------------------------------
        # 3. URL ACCESS CONTROL
        # ---------------------------------------------------------
        
        # Get the current URL name
        try:
            current_url = resolve(request.path_info).url_name
            current_namespace = resolve(request.path_info).namespace
            
            # Build full URL name with namespace
            if current_namespace:
                full_url_name = f"{current_namespace}:{current_url}"
            else:
                full_url_name = current_url
                
        except:
            current_url = None
            full_url_name = None
        
        # Check if URL starts with public prefix
        is_public_prefix = any(
            request.path_info.startswith(prefix) 
            for prefix in self.PUBLIC_PREFIXES
        )
        
        # Check if URL is an API endpoint
        is_api_endpoint = any(
            request.path_info.startswith(prefix)
            for prefix in self.API_PREFIXES
        )
        
        # Check if URL is a file/attachment endpoint
        is_file_endpoint = any(
            request.path_info.startswith(prefix)
            for prefix in self.FILE_ENDPOINTS
        )
        
        # Check if URL is a conversion endpoint
        is_conversion_endpoint = any(
            '/convert-pdf/' in request.path_info and request.path_info.startswith(prefix)
            for prefix in self.CONVERSION_ENDPOINTS
        )
        
        # Check if URL is in public list
        is_public_url = (
            current_url in self.PUBLIC_URLS or 
            full_url_name in self.PUBLIC_URLS
        )
        
        # Check if URL requires pending verification
        is_pending_verification_url = (
            current_url in self.PENDING_VERIFICATION_URLS or
            full_url_name in self.PENDING_VERIFICATION_URLS
        )
        
        # Check if user is authenticated (variable might have been cleared by flush above)
        user_id = request.session.get('user_id')
        pending_verification_user_id = request.session.get('pending_verification_user_id')
        
        # If URL requires pending verification, allow if pending verification session exists
        if is_pending_verification_url:
            if pending_verification_user_id:
                # Allow access with pending verification
                response = self.get_response(request)
                return response
            elif user_id:
                # Already fully authenticated, redirect to dashboard
                return redirect('dashboard:admin_dashboard')
            else:
                # No session at all, redirect to login
                return redirect('login')
        
        # If URL requires auth and user is not logged in
        if not is_public_prefix and not is_public_url and not user_id:
            # For API endpoints, return JSON 403 error
            if is_api_endpoint:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentication required. Please log in to access this resource.'
                }, status=403)
            
            # Check if there's a stored current page in session
            # This helps detect if session just expired vs. never existed
            last_page = request.session.get('current_page')
            
            # If trying to access the same page they were just on (refresh scenario)
            # This means session might have expired naturally or hard refresh cleared cookie
            if last_page and request.path_info == last_page:
                # For page refresh with expired session, redirect to login
                messages.warning(request, 'Your session has expired. Please log in again.')
                return redirect('login')
            
            # If no session/last_page (never logged in or on public page)
            # User is trying to access protected page directly
            if not last_page:
                # Check referer to see if coming from public page
                referer = request.META.get('HTTP_REFERER', '')
                base_url = f"{request.scheme}://{request.get_host()}/"
                
                # If no referer (typed URL) or referer is from same site (navigating from public page)
                # Redirect to access denied page
                if not referer or referer.startswith(base_url):
                    # Add message before redirecting
                    if not messages.get_messages(request):
                        messages.warning(request, 'Access denied. Please log in to access this page.')
                    return redirect('access_denied')
                else:
                    # External referer - redirect to login
                    messages.warning(request, 'Please log in to access this page.')
                    return redirect('login')
            
            # If there is a last_page but trying to access different URL (URL manipulation while logged in)
            # Redirect back to last known page to prevent unauthorized access
            if last_page and request.path_info != last_page:
                messages.warning(request, 'Please use the navigation menu to access pages.')
                return HttpResponseRedirect(last_page)
        
        # If user IS logged in and accessing file/attachment endpoints
        # Always allow these through without redirection (for <img> tags, downloads, etc.)
        if user_id and (is_file_endpoint or is_conversion_endpoint):
            response = self.get_response(request)
            return response
        
        # If user IS logged in and accessing API endpoints directly
        if user_id and is_api_endpoint:
            # Get the last valid page from session
            last_page = request.session.get('current_page')
            
            # Check if this is a direct browser access (not AJAX/fetch)
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            is_fetch = request.headers.get('Sec-Fetch-Mode') == 'cors'
            is_fetch_dest = request.headers.get('Sec-Fetch-Dest') in ['empty', 'fetch']
            accept_header = request.headers.get('Accept', '')
            is_json_request = 'application/json' in accept_header
            
            # If accessing API directly in browser (not via AJAX/fetch)
            if not is_ajax and not is_fetch and not is_fetch_dest and not is_json_request and last_page:
                # Redirect to last page instead of showing raw JSON
                messages.warning(request, 'Please use the application interface to access data.')
                return HttpResponseRedirect(last_page)
        
        # If user IS logged in on regular pages (not API)
        if user_id and not is_public_prefix and not is_public_url and not is_api_endpoint:
            # Allow logged-in users to access any page directly (no referer check)
            # Just update current_page for navigation tracking
            request.session['current_page'] = request.path_info
        
        # Continue with request
        response = self.get_response(request)
        
        # Add cache control headers to prevent caching of authenticated pages
        if user_id and not is_public_prefix and not is_public_url:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response