import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from apps.communications.utils import process_attachment
from io import BytesIO
from PIL import Image

# Create a test image
test_img = Image.new('RGB', (100, 100), color='red')
img_bytes = BytesIO()
test_img.save(img_bytes, format='PNG')
img_bytes.seek(0)

print(f"Test image size: {len(img_bytes.getvalue())} bytes")

# Create a mock file object
class MockFile:
    def __init__(self, data):
        self.data = data
        self.pos = 0
    
    def read(self):
        return self.data

mock_file = MockFile(img_bytes.getvalue())

try:
    result = process_attachment(mock_file, 'test.png')
    print(f"Success! Result: {result}")
    data, content_type, filename, size = result
    print(f"  - Data size: {len(data)}")
    print(f"  - Content type: {content_type}")
    print(f"  - Filename: {filename}")
    print(f"  - Size field: {size}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
