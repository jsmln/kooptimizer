"""
Authentication Middleware
Protects all URLs except public ones from unauthorized access
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import resolve
from django.http import HttpResponseRedirect, JsonResponse


class AuthenticationMiddleware:
    """
    Middleware to ensure users are authenticated before accessing protected pages.
    Shows access denied page for unauthenticated users.
    Prevents manual URL typing by keeping users on their current page.
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
        
        # Check if user is authenticated
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
            
            # For regular pages, show access denied page
            return render(request, 'access_denied.html', status=403)
        
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
            # Check if this is a direct URL access (typed in browser)
            referer = request.META.get('HTTP_REFERER', '')
            is_direct_access = not referer or not referer.startswith(request.build_absolute_uri('/'))
            
            # Get the last valid page from session
            last_page = request.session.get('current_page')
            
            # Only redirect if ALL these conditions are met:
            # 1. No referer (direct access)
            # 2. We have a previously stored page
            # 3. The new page is different from the stored page
            # 4. There IS a referer but it's external (to prevent hijacking)
            # 5. NOT the first access in this session (allow initial navigation)
            
            # Check if this is likely the first meaningful navigation in the session
            # (dashboard pages are often the first page after login)
            is_first_navigation = last_page is None or last_page == '/dashboard/' or 'dashboard' in last_page
            
            # If user has no referer but is making their first navigation, allow it
            # This handles PWA launches and direct bookmarks
            if is_direct_access and is_first_navigation:
                # Allow and update current page
                request.session['current_page'] = request.path_info
            elif is_direct_access and last_page and last_page != request.path_info and referer == '':
                # Only block if there's truly NO referer at all (manual URL typing)
                # But still allow if coming from a bookmark or PWA
                # Check if this might be a legitimate navigation (has session activity)
                session_age = request.session.get('_session_activity_count', 0)
                request.session['_session_activity_count'] = session_age + 1
                
                # If session is new (< 3 requests), likely PWA or bookmark - allow it
                if session_age < 3:
                    request.session['current_page'] = request.path_info
                else:
                    # Established session with manual URL typing - redirect
                    messages.warning(request, 'Please use the navigation menu to access pages.')
                    return HttpResponseRedirect(last_page)
            else:
                # Normal navigation with referer - update current page
                request.session['current_page'] = request.path_info
        
        # Continue with request
        response = self.get_response(request)
        return response
