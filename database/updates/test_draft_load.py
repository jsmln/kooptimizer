import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.communications.models import Announcement
import json

# Test getting draft
try:
    result = Announcement.get_draft_by_id(3)
    if result:
        print("✓ Draft loaded successfully:")
        print(json.dumps(result, indent=2, default=str))
    else:
        print("✗ No draft found with ID 3")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
