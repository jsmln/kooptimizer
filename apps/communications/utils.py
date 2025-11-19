import io
from PIL import Image
import gzip
import mimetypes
from io import BytesIO
import subprocess
import tempfile
import os

# Max attachment size per send (4 MB - Brevo API limit for attachments)
MAX_ATTACHMENT_SIZE = 4 * 1024 * 1024

def convert_docx_to_pdf(docx_bytes):
    """
    Convert DOCX bytes to PDF using unoconv (LibreOffice).
    Returns PDF bytes or None if conversion fails.
    """
    try:
        # Try using subprocess with LibreOffice if available
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_input:
            temp_input.write(docx_bytes)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Try using soffice (LibreOffice) for conversion
            subprocess.run([
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(temp_output_path),
                temp_input_path
            ], check=True, timeout=30, capture_output=True)
            
            # LibreOffice creates file with same name but .pdf extension
            libreoffice_output = temp_input_path.rsplit('.', 1)[0] + '.pdf'
            if os.path.exists(libreoffice_output):
                with open(libreoffice_output, 'rb') as f:
                    pdf_bytes = f.read()
                os.remove(libreoffice_output)
                return pdf_bytes
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # LibreOffice not available, try pure Python fallback
            return convert_with_reportlab(docx_bytes, 'docx')
        finally:
            # Cleanup temp files
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
                
    except Exception as e:
        print(f"DOCX to PDF conversion failed: {e}")
        return None


def convert_xlsx_to_pdf(xlsx_bytes):
    """
    Convert XLSX bytes to PDF using LibreOffice or reportlab fallback.
    Returns PDF bytes or None if conversion fails.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_input:
            temp_input.write(xlsx_bytes)
            temp_input_path = temp_input.name
        
        try:
            # Try using soffice (LibreOffice) for conversion
            subprocess.run([
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(temp_input_path),
                temp_input_path
            ], check=True, timeout=30, capture_output=True)
            
            libreoffice_output = temp_input_path.rsplit('.', 1)[0] + '.pdf'
            if os.path.exists(libreoffice_output):
                with open(libreoffice_output, 'rb') as f:
                    pdf_bytes = f.read()
                os.remove(libreoffice_output)
                return pdf_bytes
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # LibreOffice not available, try pure Python fallback
            return convert_with_reportlab(xlsx_bytes, 'xlsx')
        finally:
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
                
    except Exception as e:
        print(f"XLSX to PDF conversion failed: {e}")
        return None


def convert_with_reportlab(file_bytes, file_type):
    """
    Fallback conversion using reportlab (text-only, basic).
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        
        pdf_file = BytesIO()
        
        if file_type == 'xlsx':
            from openpyxl import load_workbook
            xlsx_file = BytesIO(file_bytes)
            wb = load_workbook(xlsx_file)
            ws = wb.active
            
            c = canvas.Canvas(pdf_file, pagesize=landscape(A4))
            width, height = landscape(A4)
            y = height - 40
            
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                if row_text.strip():
                    text_obj = c.beginText(40, y)
                    text_obj.setFont("Helvetica", 9)
                    text_obj.textLines(row_text, maxWidth=width - 80)
                    c.drawText(text_obj)
                    y -= 15
                    if y < 40:
                        c.showPage()
                        y = height - 40
        elif file_type == 'docx':
            from docx import Document
            docx_file = BytesIO(file_bytes)
            doc = Document(docx_file)
            
            c = canvas.Canvas(pdf_file, pagesize=A4)
            width, height = A4
            y = height - 40
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_obj = c.beginText(40, y)
                    text_obj.setFont("Helvetica", 10)
                    text_obj.textLines(para.text, maxWidth=width - 80)
                    c.drawText(text_obj)
                    y -= 20
                    if y < 40:
                        c.showPage()
                        y = height - 40
        
        c.save()
        pdf_file.seek(0)
        return pdf_file.getvalue()
    except Exception as e:
        print(f"ReportLab fallback conversion failed: {e}")
        return None

def can_convert_to_pdf(content_type):
    """Check if file type can be converted to PDF."""
    convertible_types = [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
    ]
    return content_type in convertible_types

def convert_to_pdf(file_bytes, filename, content_type):
    """
    Convert office documents to PDF.
    Returns (pdf_bytes, success) tuple.
    """
    if 'wordprocessingml' in content_type or content_type == 'application/msword':
        pdf_bytes = convert_docx_to_pdf(file_bytes)
        if pdf_bytes:
            return pdf_bytes, True
    elif 'spreadsheet' in content_type or content_type == 'application/vnd.ms-excel':
        pdf_bytes = convert_xlsx_to_pdf(file_bytes)
        if pdf_bytes:
            return pdf_bytes, True
    
    return None, False

def process_attachment(file_obj, filename):
    """
    Accepts a Django UploadedFile (file_obj) and filename.
    - If image: resize/re-encode to reduce size.
    - If non-image: try gzip compress; if still > MAX, reject.
    Returns tuple: (bytes_data, content_type, final_filename, size)
    """
    # Read raw bytes
    raw = file_obj.read()
    size = len(raw)

    # Quick reject if already over hard limit
    if size > MAX_ATTACHMENT_SIZE * 4:
        # If file is extremely large, bail out early
        raise ValueError('File too large')

    # Try to detect image using Pillow
    try:
        img_test = Image.open(io.BytesIO(raw))
        img_test.verify()  # Verify it's a valid image
        kind = img_test.format  # Get format string
    except Exception:
        kind = None
    if kind:
        # Process image
        img = Image.open(io.BytesIO(raw))
        img_format = 'JPEG' if img.mode in ('RGB', 'L', 'RGBA') else img.format or 'JPEG'

        # Resize if width > 1920 or height > 1920
        max_dim = 1920
        if max(img.size) > max_dim:
            ratio = max_dim / float(max(img.size))
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        out = io.BytesIO()
        # Save as JPEG to reduce size; use quality tradeoff
        save_kwargs = {'format': 'JPEG', 'quality': 78, 'optimize': True}
        if img.mode in ('RGBA', 'LA'):
            # convert to RGB background-white
            bg = Image.new('RGB', img.size, (255,255,255))
            bg.paste(img, mask=img.split()[3])
            img = bg

        img.save(out, **save_kwargs)
        data = out.getvalue()
        final_size = len(data)
        if final_size > MAX_ATTACHMENT_SIZE:
            # try reducing quality
            out = io.BytesIO()
            img.save(out, format='JPEG', quality=65, optimize=True)
            data = out.getvalue()
            final_size = len(data)

        if final_size > MAX_ATTACHMENT_SIZE:
            raise ValueError('Image could not be reduced below 25MB')

        content_type = 'image/jpeg'
        final_filename = filename.rsplit('.', 1)[0] + '.jpg'
        return data, content_type, final_filename, final_size

    else:
        # Non-image: prefer returning raw bytes with a sensible content-type so browsers can preview (e.g., PDFs)
        # Use provided upload content_type when available (Django UploadedFile provides it)
        provided_ct = getattr(file_obj, 'content_type', None)
        import mimetypes
        if not provided_ct:
            provided_ct, _ = mimetypes.guess_type(filename)

        # If file is small enough, return raw bytes and preserve content-type
        if size <= MAX_ATTACHMENT_SIZE:
            content_type = provided_ct or 'application/octet-stream'
            return raw, content_type, filename, size

        # If too large, attempt gzip compression as a last resort
        compressed = gzip.compress(raw)
        if len(compressed) <= MAX_ATTACHMENT_SIZE:
            content_type = 'application/gzip'
            final_filename = filename + '.gz'
            return compressed, content_type, final_filename, len(compressed)

        # otherwise reject
        raise ValueError('File too large and cannot be reduced below 25MB')
