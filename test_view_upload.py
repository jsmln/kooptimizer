import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

# Now test the view logic in isolation
from io import BytesIO
from PIL import Image
from apps.communications.utils import process_attachment
from apps.users.models import User
from apps.communications.models import Message
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

# Create a test image file
test_img = Image.new('RGB', (200, 200), color='green')
img_bytes = BytesIO()
test_img.save(img_bytes, format='PNG')
img_bytes.seek(0)
img_bytes.name = 'test_image.png'

# Create mock request
factory = RequestFactory()
request = factory.post('/communications/api/message/send/')

# Add session
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session['user_id'] = 1
request.session['role'] = 'admin'
request.session.save()

# Add FILES
request.FILES = {'attachment': img_bytes}
request.POST = {'receiver_id': '6', 'message': 'Test with attachment'}
request.content_type = 'multipart/form-data'

print("Simulating file upload processing...")
try:
    upload = img_bytes
    print(f"  Upload object: {upload}")
    print(f"  Upload name: {getattr(upload, 'name', 'N/A')}")
    print(f"  Upload size: {len(img_bytes.getvalue())}")
    
    # Reset seek
    upload.seek(0)
    
    data_bytes, content_type, final_filename, final_size = process_attachment(upload, upload.name)
    print(f"  Processed successfully")
    print(f"    - Bytes: {len(data_bytes)}")
    print(f"    - Type: {content_type}")
    print(f"    - Filename: {final_filename}")
    print(f"    - Size: {final_size}")
    
    # Check latest message
    latest_msg = Message.objects.all().order_by('-message_id').first()
    if latest_msg:
        print(f"\nLatest message in DB:")
        print(f"  ID: {latest_msg.message_id}")
        print(f"  Text: {latest_msg.message}")
        print(f"  Attachment exists: {bool(latest_msg.attachment)}")
        print(f"  Attachment size stored: {latest_msg.attachment_size}")
        print(f"  Attachment filename: {latest_msg.attachment_filename}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
