from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
import json
from apps.core.services.ocr_service import optiic_service

def databank_management_view(request):
    try:
        with connection.cursor() as cursor:
            # UPDATED: Matches your specific SQL function name
            cursor.execute("SELECT * FROM sp_get_all_cooperatives()")
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                # Convert rows to a list of dictionaries
                cooperatives = [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                cooperatives = []

        context = {
            'cooperatives': cooperatives,
            'total_count': len(cooperatives)
        }
        return render(request, 'databank/databank_management.html', context)
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'databank/databank_management.html', {
            'cooperatives': [],
            'error': f"Database Error: {str(e)}"
        })
    

def view_attachment(request, coop_id, doc_type):
    # Placeholder for viewing attachments. 
    # You need to implement the actual file serving logic here.
    # Logic to fetch file path based on coop_id and doc_type
    # Example:
    # file_path = get_file_path(coop_id, doc_type)
    # return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    return HttpResponse("File viewing logic not implemented yet.", status=501)

@require_http_methods(["POST"])
def process_ocr(request):
    try:
        if 'image' in request.FILES:
            result = optiic_service.process_image_file(request.FILES['image'])
        elif 'url' in request.POST:
            result = optiic_service.process_image_url(request.POST.get('url'))
        elif 'base64' in request.POST:
            result = optiic_service.process_base64_image(request.POST.get('base64'))
        else:
            data = json.loads(request.body)
            if 'base64' in data:
                result = optiic_service.process_base64_image(data['base64'])
            elif 'url' in data:
                result = optiic_service.process_image_url(data['url'])
            else:
                return JsonResponse({'success': False, 'error': 'No image data'}, status=400)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def add_cooperative(request):
    try:
        data = json.loads(request.body)
        
        with connection.cursor() as cursor:
            # UPDATED: Your SQL function accepts exactly 9 arguments
            cursor.execute("""
                SELECT sp_create_cooperative(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                data.get('staff_id'),
                data.get('cooperative_name'),
                data.get('category'),
                data.get('district'),
                data.get('address'),
                data.get('mobile_number'),
                data.get('email_address'),
                data.get('cda_registration_number'),
                data.get('cda_registration_date')
            ])
            
            # Retrieve the new ID returned by the function
            new_id = cursor.fetchone()[0]
            
        return JsonResponse({
            'success': True, 
            'coop_id': new_id, 
            'message': 'Cooperative added successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_cooperative(request, coop_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_get_all_cooperatives()")
            columns = [col[0] for col in cursor.description]
            
            target_coop = None
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                if row_dict['coop_id'] == coop_id:
                    target_coop = row_dict
                    break
            
            if target_coop:
                return JsonResponse({'success': True, 'data': target_coop})
            else:
                return JsonResponse({'success': False, 'error': 'Cooperative not found'}, status=404)
                
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["PUT", "POST"])
def update_cooperative(request, coop_id):
    try:
        data = json.loads(request.body)
        with connection.cursor() as cursor:
            # UPDATED: Using 'CALL' because your SQL defines this as a PROCEDURE, not FUNCTION
            cursor.execute("""
                CALL sp_update_cooperative_profile(
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                coop_id,
                data.get('address'),
                data.get('mobile_number'),
                data.get('email_address'),
                data.get('assets', 0),
                data.get('paid_up_capital', 0),
                data.get('net_surplus', 0)
            ])
            
        return JsonResponse({'success': True, 'message': 'Cooperative updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["DELETE", "POST"])
def delete_cooperative(request, coop_id):
    try:
        with connection.cursor() as cursor:
            # UPDATED: Using 'CALL' for stored procedure
            cursor.execute("CALL sp_delete_cooperative(%s)", [coop_id])
            
        return JsonResponse({'success': True, 'message': 'Cooperative deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@require_http_methods(["POST"])
def restore_cooperative(request, coop_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE cooperatives SET is_active = TRUE, updated_at = NOW() WHERE coop_id = %s", [coop_id])
        return JsonResponse({'success': True, 'message': 'Cooperative restored successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)