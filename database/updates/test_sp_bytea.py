import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection
from apps.communications.utils import process_attachment
from io import BytesIO
from PIL import Image

# Create a test image
test_img = Image.new('RGB', (100, 100), color='blue')
img_bytes = BytesIO()
test_img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# Process it through our attachment processor
class MockFile:
    def __init__(self, data):
        self.data = data
    
    def read(self):
        return self.data

mock_file = MockFile(img_bytes.getvalue())
data_bytes, content_type, filename, final_size = process_attachment(mock_file, 'test.png')

print(f"Processed attachment:")
print(f"  Size: {len(data_bytes)} bytes")
print(f"  Content-Type: {content_type}")
print(f"  Filename: {filename}")

# Now try calling sp_send_message with bytea
try:
    with connection.cursor() as cursor:
        # Use psycopg3/psycopg2 binary adapter for bytea
        cursor.execute(
            "SELECT * FROM sp_send_message(%s, %s, %s, %s, %s, %s, %s);",
            [1, 6, "Test message with attachment", data_bytes, filename, content_type, final_size]
        )
        row = cursor.fetchone()
        
    if row:
        print(f"\nMessage sent successfully!")
        msg_id, sender_id, receiver_id, msg_text, attachment, att_filename, att_content_type, att_size, sent_at = row
        print(f"  Message ID: {msg_id}")
        print(f"  Attachment bytes stored: {len(attachment) if attachment else 0}")
        print(f"  Attachment filename: {att_filename}")
        print(f"  Attachment size: {att_size}")
    else:
        print("Failed: no row returned")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
