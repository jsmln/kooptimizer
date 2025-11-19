from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
import json
from apps.core.services.ocr_service import optiic_service


def databank_management_view(request):
    """Main databank management page with cooperative data"""
    try:
        with connection.cursor() as cursor:
            # Call stored procedure to get all cooperatives with full details
            cursor.execute("SELECT * FROM sp_display_cooperatives()")
            columns = [col[0] for col in cursor.description]
            cooperatives = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        context = {
            'cooperatives': cooperatives,
            'total_count': len(cooperatives)
        }
        return render(request, 'databank/databank_management.html', context)
    except Exception as e:
        print(f"Error fetching cooperatives: {e}")
        return render(request, 'databank/databank_management.html', {
            'cooperatives': [],
            'total_count': 0,
            'error': str(e)
        })


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


@require_http_methods(["POST"])
def add_cooperative(request):
    """Add a new cooperative using stored procedure"""
    try:
        data = json.loads(request.body)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM sp_add_cooperative(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                data.get('staff_id'),
                data.get('cooperative_name'),
                data.get('address'),
                data.get('mobile_number'),
                data.get('email_address'),
                data.get('cda_registration_number'),
                data.get('cda_registration_date'),
                data.get('lccdc_membership', False),
                data.get('lccdc_membership_date'),
                data.get('operation_area'),
                data.get('business_activity'),
                data.get('board_of_directors_count'),
                data.get('salaried_employees_count'),
                data.get('coc_renewal', False),
                data.get('cote_renewal', False),
                data.get('category'),
                data.get('district'),
                data.get('approval_status', 'pending')
            ])
            
            result = cursor.fetchone()
            
        return JsonResponse({
            'success': True,
            'coop_id': result[0] if result else None,
            'message': 'Cooperative added successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_cooperative(request, coop_id):
    """Get cooperative details by ID"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_display_cooperatives(%s)", [coop_id])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if row:
                cooperative = dict(zip(columns, row))
                return JsonResponse({
                    'success': True,
                    'data': cooperative
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Cooperative not found'
                }, status=404)
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["PUT", "POST"])
def update_cooperative(request, coop_id):
    """Update cooperative using stored procedure"""
    try:
        data = json.loads(request.body)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM sp_edit_cooperative(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                coop_id,
                data.get('staff_id'),
                data.get('cooperative_name'),
                data.get('address'),
                data.get('mobile_number'),
                data.get('email_address'),
                data.get('cda_registration_number'),
                data.get('cda_registration_date'),
                data.get('lccdc_membership'),
                data.get('lccdc_membership_date'),
                data.get('operation_area'),
                data.get('business_activity'),
                data.get('board_of_directors_count'),
                data.get('salaried_employees_count'),
                data.get('coc_renewal'),
                data.get('cote_renewal'),
                data.get('category'),
                data.get('district')
            ])
            
            result = cursor.fetchone()
            
        return JsonResponse({
            'success': True,
            'message': 'Cooperative updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["DELETE", "POST"])
def delete_cooperative(request, coop_id):
    """Mark cooperative as inactive (soft delete)"""
    try:
        with connection.cursor() as cursor:
            # Soft delete: mark as inactive
            cursor.execute("SELECT * FROM sp_delete_cooperative(%s, FALSE)", [coop_id])
            result = cursor.fetchone()
            
        return JsonResponse({
            'success': True,
            'message': 'Cooperative marked as inactive'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def restore_cooperative(request, coop_id):
    """Restore inactive cooperative"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE cooperatives 
                SET is_active = TRUE, updated_at = NOW()
                WHERE coop_id = %s
            """, [coop_id])
            
        return JsonResponse({
            'success': True,
            'message': 'Cooperative restored successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
