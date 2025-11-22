"""
Test script to debug email announcement saving
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.communications.models import Announcement

# Test saving a simple email announcement as draft
print("Testing email announcement save...")

try:
    result = Announcement.save_announcement(
        title="Test Email Announcement",
        content="This is a test email content",
        ann_type="e-mail",  # E-MAIL type with hyphen
        status="draft",
        scope="cooperative",
        creator_id=1,  # Replace with valid user_id
        creator_role="admin",
        coop_ids=[1],  # Replace with valid coop_id
        officer_ids=[],
        announcement_id=None,
        scheduled_time=None
    )
    
    if result:
        print(f"✓ SUCCESS! Announcement saved with ID: {result}")
    else:
        print("✗ FAILED! save_announcement returned None")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
