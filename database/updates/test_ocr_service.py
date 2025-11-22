"""
Test script for OCR service
Run this to verify Optiic API integration is working
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
import django
django.setup()

from apps.core.services.ocr_service import optiic_service


def test_ocr_url():
    """Test OCR with a sample image URL"""
    print("Testing OCR with sample URL...")
    print("-" * 50)
    
    # Sample image from Optiic documentation
    test_url = "https://optiic.dev/assets/images/samples/we-love-optiic.png"
    
    result = optiic_service.process_image_url(test_url)
    
    print(f"Success: {result['success']}")
    print(f"Text: {result['text']}")
    print(f"Language: {result['language']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    print("-" * 50)
    
    if result['success'] and result['text']:
        print("✓ OCR service is working correctly!")
        return True
    else:
        print("✗ OCR service test failed")
        return False


def test_ocr_base64():
    """Test OCR with a base64 sample"""
    print("\nTesting OCR with base64 sample...")
    print("-" * 50)
    
    # Small 1x1 PNG image in base64 (for testing)
    test_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    result = optiic_service.process_base64_image(test_base64)
    
    print(f"Success: {result['success']}")
    print(f"Text: {result['text']}")
    print(f"Language: {result['language']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    print("-" * 50)
    
    return result['success']


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("OCR SERVICE TEST")
    print("=" * 50)
    
    # Test URL processing
    url_test_passed = test_ocr_url()
    
    # Test base64 processing
    # base64_test_passed = test_ocr_base64()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"URL Processing: {'PASSED ✓' if url_test_passed else 'FAILED ✗'}")
    # print(f"Base64 Processing: {'PASSED ✓' if base64_test_passed else 'FAILED ✗'}")
    print("=" * 50)
    
    print("\nNote: If tests fail, check your OPTIIC_API_KEY in settings.py")
    print("You can use 'test_api_key' for testing purposes.")
