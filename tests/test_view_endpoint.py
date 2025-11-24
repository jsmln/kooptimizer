import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import RequestFactory
from apps.communications.views import get_announcement_details

# Create a mock request with session
factory = RequestFactory()
request = factory.get('/api/announcement/35/')
request.session = {
    'user_id': 1,
    'role': 'admin'
}

# Call the view
try:
    response = get_announcement_details(request, announcement_id=35)
    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.content.decode('utf-8')}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
