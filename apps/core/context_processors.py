from django.conf import settings

def webpush_processor(request):
    return {'webpush_settings': getattr(settings, 'WEBPUSH_SETTINGS', {})}