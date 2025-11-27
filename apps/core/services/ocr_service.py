"""
OCR Service: Smart Hybrid Implementation
Primary: Optiic.dev
Fallback: OCR.Space
Optimization: Circuit Breaker with Daily Reset.
"""

import requests
import base64
from typing import Dict, Any
from django.conf import settings
from django.utils import timezone 

class UnifiedOCRService:
    # Optiic Configuration
    OPTIIC_URL = "https://api.optiic.dev/process"
    
    # OCR.Space Configuration
    OCR_SPACE_URL = "https://api.ocr.space/parse/image"

    def __init__(self):
        self.optiic_key = getattr(settings, 'OPTIIC_API_KEY', 'test_key')
        self.ocr_space_key = getattr(settings, 'OCR_SPACE_API_KEY', '')
        
        # CIRCUIT BREAKER STATE
        self.optiic_exhausted = False 
        self.exhausted_date = None # Tracks WHICH day we hit the limit

    # ==========================================
    # INTERNAL: RESET LOGIC
    # ==========================================
    def _check_and_reset_breaker(self):
        """
        Checks if we are in a new day since the limit was hit.
        If so, reset the circuit breaker to try Optiic again.
        """
        if self.optiic_exhausted and self.exhausted_date:
            today = timezone.now().date()
            if today > self.exhausted_date:
                print(f"New day detected ({today}). Resetting Optiic limit.")
                self.optiic_exhausted = False
                self.exhausted_date = None

    def _trigger_circuit_breaker(self, error_msg):
        """Activates the breaker and records the date"""
        self.optiic_exhausted = True
        self.exhausted_date = timezone.now().date()
        print(f"Optiic Limit Reached ({error_msg}). Disabling Optiic for the rest of {self.exhausted_date}.")

    # ==========================================
    # PUBLIC METHODS
    # ==========================================

    def process_image_url(self, image_url: str) -> Dict[str, Any]:
        # 1. Check if it's a new day and reset if needed
        self._check_and_reset_breaker()

        # 2. Check Circuit Breaker
        if self.optiic_exhausted:
            print("Optiic exhausted (skipped). Using OCR.Space...")
            return self._call_ocr_space_url(image_url)

        # 3. Try Optiic
        result = self._call_optiic_url(image_url)
        
        # 4. Check Limit
        if self._is_limit_reached(result):
            self._trigger_circuit_breaker(result['error'])
            return self._call_ocr_space_url(image_url)
            
        return result

    def process_image_file(self, image_file) -> Dict[str, Any]:
        start_pos = image_file.tell() if hasattr(image_file, 'tell') else 0

        # 1. Check/Reset Day
        self._check_and_reset_breaker()

        # 2. Check Circuit Breaker
        if self.optiic_exhausted:
            print("Optiic exhausted (skipped). Using OCR.Space...")
            return self._call_ocr_space_file(image_file)

        # 3. Try Optiic
        result = self._call_optiic_file(image_file)

        # 4. Check Limit
        if self._is_limit_reached(result):
            self._trigger_circuit_breaker(result['error'])
            
            # Reset file pointer
            if hasattr(image_file, 'seek'):
                image_file.seek(start_pos)
            
            return self._call_ocr_space_file(image_file)

        return result

    def process_base64_image(self, base64_data: str) -> Dict[str, Any]:
        if ',' in base64_data:
            clean_base64 = base64_data.split(',', 1)[1]
        else:
            clean_base64 = base64_data

        # 1. Check/Reset Day
        self._check_and_reset_breaker()

        # 2. Check Circuit Breaker
        if self.optiic_exhausted:
            print("Optiic exhausted (skipped). Using OCR.Space...")
            return self._call_ocr_space_base64(f"data:image/png;base64,{clean_base64}")

        # 3. Try Optiic
        result = self._call_optiic_base64(clean_base64)

        # 4. Check Limit
        if self._is_limit_reached(result):
            self._trigger_circuit_breaker(result['error'])
            return self._call_ocr_space_base64(f"data:image/png;base64,{clean_base64}")

        return result

    # ==========================================
    # HELPER: ERROR CHECKING
    # ==========================================

    def _is_limit_reached(self, result: Dict) -> bool:
        if result['success']:
            return False
            
        error_msg = str(result.get('error', '')).lower()
        conditions = [
            '429' in error_msg,
            'limit' in error_msg,
            'exceeded' in error_msg,
            '5/5' in error_msg
        ]
        return any(conditions)

    # ==========================================
    # PROVIDER 1: OPTIIC IMPLEMENTATION
    # ==========================================

    def _call_optiic_url(self, url):
        try:
            resp = requests.post(
                self.OPTIIC_URL,
                json={'apiKey': self.optiic_key, 'url': url, 'mode': 'ocr'},
                headers={'Content-Type': 'application/json'},
                timeout=90  # <--- CHANGED FROM 30 TO 90
            )
            return self._parse_optiic_response(resp)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _call_optiic_file(self, image_file):
        try:
            content = image_file.read()
            files = {'image': ('image.png', content, 'image/png')}
            data = {'apiKey': self.optiic_key, 'mode': 'ocr'}
            # <--- CHANGED FROM 30 TO 90
            resp = requests.post(self.OPTIIC_URL, files=files, data=data, timeout=90) 
            return self._parse_optiic_response(resp)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _call_optiic_base64(self, clean_base64):
        try:
            image_content = base64.b64decode(clean_base64)
            files = {'image': ('clipboard.png', image_content, 'image/png')}
            data = {'apiKey': self.optiic_key, 'mode': 'ocr'}
            # <--- CHANGED FROM 30 TO 90
            resp = requests.post(self.OPTIIC_URL, files=files, data=data, timeout=90)
            return self._parse_optiic_response(resp)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_optiic_response(self, response):
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'text': data.get('text', ''),
                'language': data.get('language', 'unknown'),
                'provider': 'optiic',
                'error': None
            }
        return {
            'success': False, 
            'error': f"Optiic API error: {response.status_code} - {response.text}"
        }

    # ==========================================
    # PROVIDER 2: OCR.SPACE IMPLEMENTATION
    # ==========================================

    def _call_ocr_space_url(self, url):
        payload = {
            'url': url,
            'isOverlayRequired': False,
            'apikey': self.ocr_space_key,
            'language': 'eng',
            'OCRExitCode': 1
        }
        try:
            resp = requests.post(self.OCR_SPACE_URL, data=payload, timeout=30)
            return self._parse_ocr_space_response(resp)
        except Exception as e:
            return {'success': False, 'error': f"OCR.Space Error: {str(e)}"}

    def _call_ocr_space_file(self, image_file):
        try:
            content = image_file.read()
            payload = {'isOverlayRequired': False, 'apikey': self.ocr_space_key, 'language': 'eng'}
            files = {'file': ('image.png', content, 'image/png')}
            resp = requests.post(self.OCR_SPACE_URL, files=files, data=payload, timeout=30)
            return self._parse_ocr_space_response(resp)
        except Exception as e:
            return {'success': False, 'error': f"OCR.Space Error: {str(e)}"}

    def _call_ocr_space_base64(self, base64_string):
        payload = {
            'base64Image': base64_string,
            'isOverlayRequired': False,
            'apikey': self.ocr_space_key,
            'language': 'eng'
        }
        try:
            resp = requests.post(self.OCR_SPACE_URL, data=payload, timeout=30)
            return self._parse_ocr_space_response(resp)
        except Exception as e:
            return {'success': False, 'error': f"OCR.Space Error: {str(e)}"}

    def _parse_ocr_space_response(self, response):
        try:
            res = response.json()
            if res.get('OCRExitCode') == 1:
                parsed_results = res.get('ParsedResults', [])
                extracted_text = ""
                if parsed_results:
                    extracted_text = parsed_results[0].get('ParsedText', '')
                
                return {
                    'success': True,
                    'text': extracted_text,
                    'language': 'eng',
                    'provider': 'ocr_space',
                    'error': None
                }
            
            error_msg = res.get('ErrorMessage')
            if isinstance(error_msg, list):
                error_msg = ", ".join(error_msg)
            return {'success': False, 'error': f"OCR.Space API Error: {error_msg or 'Unknown Error'}"}
        except Exception as e:
            return {'success': False, 'error': f"Failed to parse OCR.Space response: {str(e)}"}

# Singleton instance
optiic_service = UnifiedOCRService()