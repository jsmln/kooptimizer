from django.apps import AppConfig


class CooperativesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cooperatives'
    
    def ready(self):
        """Activate signals when Django starts."""
        # Import signals to activate them
        import apps.cooperatives.signals

