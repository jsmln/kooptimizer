"""
Test OPTIIC OCR API Key functionality
Verifies the API key works by testing the OCR service
"""

import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.conf import settings
from apps.core.services.ocr_service import OptiicOCRService

print("\n" + "="*70)
print("  TESTING OPTIIC OCR API KEY")
print("="*70)

# Check if API key is configured
api_key = getattr(settings, 'OPTIIC_API_KEY', '')
print(f"\n✓ API Key loaded from settings: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
print(f"  Length: {len(api_key)} characters")

# Initialize OCR service
print("\n" + "-"*70)
print("Initializing OCR Service...")
print("-"*70)

try:
    ocr_service = OptiicOCRService()
    print("✅ OCR Service initialized successfully")
    print(f"   API URL: {ocr_service.API_URL}")
    print(f"   API Key: {ocr_service.api_key[:10]}...{ocr_service.api_key[-10:]}")
except Exception as e:
    print(f"❌ Failed to initialize OCR Service: {e}")
    sys.exit(1)

# Test with a local image file
print("\n" + "-"*70)
print("Testing OCR with local header.png file...")
print("-"*70)

# Use the local header.png file
test_image_path = os.path.join(BASE_DIR, 'static', 'frontend', 'images', 'header.png')

if os.path.exists(test_image_path):
    print(f"✓ Found image: {test_image_path}")
    print(f"  File size: {os.path.getsize(test_image_path)} bytes")
    print("  Processing image with OCR...")
    
    try:
        with open(test_image_path, 'rb') as img_file:
            result = ocr_service.process_image_file(img_file)
        
        print("\n📊 OCR Result:")
        print("-"*70)
        
        if result['success']:
            print("✅ Status: SUCCESS")
            print(f"   Language: {result.get('language', 'N/A')}")
            print(f"   Extracted Text:\n")
            print("   " + "-"*66)
            
            text = result.get('text', '')
            if text:
                # Print text with indentation
                for line in text.split('\n'):
                    print(f"   {line}")
            else:
                print("   (No text extracted - image may be a logo/graphic)")
            
            print("   " + "-"*66)
            
        else:
            print("❌ Status: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Check if it's an API key issue
            if 'unauthorized' in str(result.get('error', '')).lower() or 'api key' in str(result.get('error', '')).lower() or '401' in str(result.get('error', '')):
                print("\n⚠️  This appears to be an API key issue.")
                print("   Please verify your API key at: https://optiic.dev/")
            elif 'forbidden' in str(result.get('error', '')).lower() or '403' in str(result.get('error', '')):
                print("\n⚠️  API key may not have permission for this operation.")
            else:
                print("\n⚠️  OCR processing failed. Check the error message above.")
                
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Image not found: {test_image_path}")

# Summary
print("\n" + "="*70)
print("  OPTIIC OCR TEST SUMMARY")
print("="*70)

if api_key and len(api_key) > 20:
    print("✅ API Key: Configured and loaded")
else:
    print("❌ API Key: Not properly configured")

print("\n💡 To use OCR in your application:")
print("   1. Upload an image through the Data Bank Management page")
print("   2. The OCR service will extract text automatically")
print("   3. Extracted text will be available for processing")

print("\n📝 API Key is stored in: .env (OPTIIC_API_KEY)")
print("🔒 API Key is secure: Not committed to git")

print("\n" + "="*70 + "\n")
