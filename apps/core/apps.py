from django.apps import AppConfig
import sys


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        """
        Performs startup checks when Django loads.
        This ensures critical dependencies are available.
        """
        # Only run checks in the main process, not in reloader
        if 'runserver' in sys.argv and '--noreload' not in sys.argv:
            # Skip in the parent process of runserver
            import os
            if os.environ.get('RUN_MAIN') != 'true':
                return
        
        # Check for Google API client
        try:
            import googleapiclient
            print("✓ Google API client is available")
        except ImportError:
            print("\n" + "="*70)
            print("⚠ WARNING: google-api-python-client is not installed!")
            print("="*70)
            print("Google Calendar integration will not work.")
            print("\nTo fix this, run:")
            print("  pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib")
            print("\nOr install all requirements:")
            print("  pip install -r requirements.txt")
            print("="*70 + "\n")
