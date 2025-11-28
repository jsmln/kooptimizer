from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communications'
    
    def ready(self):
        """Start the announcement scheduler and activate signals when Django starts."""
        # Import signals to activate them
        import apps.communications.signals
        
        # Start scheduler in the main process (not in reloader or other processes)
        import os
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from .scheduler import start_scheduler
            start_scheduler()