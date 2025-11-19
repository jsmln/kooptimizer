from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import json
from apps.core.services.ocr_service import optiic_service


def databank_management_view(request):
    """Main databank management page"""
    return render(request, 'databank/databank_management.html')


@require_http_methods(["POST"])
def process_ocr(request):
    """
    Process OCR request from uploaded image, URL, or base64 data
    """
    try:
        # Check if it's a file upload
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            result = optiic_service.process_image_file(image_file)
            
        # Check if it's a URL
        elif 'url' in request.POST:
            image_url = request.POST.get('url')
            result = optiic_service.process_image_url(image_url)
            
        # Check if it's base64 data (clipboard/screenshot)
        elif 'base64' in request.POST:
            base64_data = request.POST.get('base64')
            result = optiic_service.process_base64_image(base64_data)
            
        # Handle JSON payload
        else:
            try:
                data = json.loads(request.body)
                if 'base64' in data:
                    result = optiic_service.process_base64_image(data['base64'])
                elif 'url' in data:
                    result = optiic_service.process_image_url(data['url'])
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No image data provided'
                    }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON payload'
                }, status=400)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)