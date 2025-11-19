"""
OCR Service using Optiic.dev API
Handles image text extraction for Data Bank Management
"""

import requests
import base64
import os
from typing import Dict, Any, Optional
from django.conf import settings


class OptiicOCRService:
    """
    Service class for Optiic OCR API integration
    """
    
    API_URL = "https://api.optiic.dev/process"
    
    def __init__(self):
        """Initialize OCR service with API key from settings"""
        self.api_key = getattr(settings, 'OPTIIC_API_KEY', 'test_api_key')
    
    def process_image_url(self, image_url: str, mode: str = 'ocr') -> Dict[str, Any]:
        """
        Process image from URL
        
        Args:
            image_url: Remote URL of the image
            mode: Processing mode (default: 'ocr')
            
        Returns:
            Dict with 'success', 'text', 'language', 'error'
        """
        try:
            payload = {
                'apiKey': self.api_key,
                'url': image_url,
                'mode': mode
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'text': result.get('text', ''),
                    'language': result.get('language', 'unknown'),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'text': '',
                    'language': '',
                    'error': f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'language': '',
                'error': str(e)
            }
    
    def process_image_file(self, image_file, mode: str = 'ocr') -> Dict[str, Any]:
        """
        Process uploaded image file
        
        Args:
            image_file: Django UploadedFile object or file-like object
            mode: Processing mode (default: 'ocr')
            
        Returns:
            Dict with 'success', 'text', 'language', 'error'
        """
        try:
            # Read file content
            if hasattr(image_file, 'read'):
                image_content = image_file.read()
                if hasattr(image_file, 'seek'):
                    image_file.seek(0)  # Reset file pointer
            else:
                with open(image_file, 'rb') as f:
                    image_content = f.read()
            
            # Prepare multipart form data
            files = {
                'image': ('image.png', image_content, 'image/png')
            }
            
            data = {
                'apiKey': self.api_key,
                'mode': mode
            }
            
            response = requests.post(
                self.API_URL,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'text': result.get('text', ''),
                    'language': result.get('language', 'unknown'),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'text': '',
                    'language': '',
                    'error': f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'language': '',
                'error': str(e)
            }
    
    def process_base64_image(self, base64_data: str, mode: str = 'ocr') -> Dict[str, Any]:
        """
        Process base64-encoded image (from clipboard or screenshot)
        
        Args:
            base64_data: Base64-encoded image string (with or without data URI prefix)
            mode: Processing mode (default: 'ocr')
            
        Returns:
            Dict with 'success', 'text', 'language', 'error'
        """
        try:
            # Remove data URI prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            
            # Decode base64 to binary
            image_content = base64.b64decode(base64_data)
            
            # Prepare multipart form data
            files = {
                'image': ('clipboard.png', image_content, 'image/png')
            }
            
            data = {
                'apiKey': self.api_key,
                'mode': mode
            }
            
            response = requests.post(
                self.API_URL,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'text': result.get('text', ''),
                    'language': result.get('language', 'unknown'),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'text': '',
                    'language': '',
                    'error': f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'language': '',
                'error': str(e)
            }


# Singleton instance
optiic_service = OptiicOCRService()
