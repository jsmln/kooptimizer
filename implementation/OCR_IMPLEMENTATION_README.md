# Data Bank Management System - OCR Integration

## Overview
This implementation adds comprehensive OCR (Optical Character Recognition) capabilities to the Kooptimizer Data Bank Management System using the Optiic.dev API. The system now includes:

1. **Database Schema Updates** - Enhanced cooperatives table structure
2. **CRUD Stored Procedures** - Complete data management across 5 tables
3. **OCR Service Backend** - Python integration with Optiic.dev API
4. **OCR Assistant UI** - Bootstrap-based slide-out drawer interface

---

## Database Changes

### Schema Modifications (cooperatives table)

**Added Columns:**
- `category` VARCHAR(100) - Type of cooperative (Credit, Service, Marketing, etc.)
- `district` VARCHAR(100) - Geographical district/zone

**Removed Columns:**
- `mobile_number` - Moved to `profile_data` table for better organization

**Indexes Created:**
- `idx_cooperatives_category` - For category-based filtering
- `idx_cooperatives_district` - For district-based filtering

### Stored Procedures Created

#### 1. `sp_add_cooperative`
Creates a new cooperative record with all related data across 5 tables:
- cooperatives (main record)
- profile_data (contact and registration info)
- financial_data (financial records)
- officers (cooperative officers as JSON array)
- members (cooperative members as JSON array)

**Usage:**
```sql
SELECT * FROM sp_add_cooperative(
    'Cooperative Name', 
    staff_id, 
    'Credit', 
    'District 1',
    -- profile data...
    -- financial data...
    -- officers JSON...
    -- members JSON...
);
```

#### 2. `sp_display_cooperatives`
Retrieves complete cooperative records with LEFT JOINs across all 5 tables. Returns:
- All cooperative information
- Profile data
- Latest financial data (by year)
- Officers (as JSON array)
- Members (as JSON array)
- Aggregate counts

**Usage:**
```sql
-- Get all cooperatives
SELECT * FROM sp_display_cooperatives();

-- Get specific cooperative
SELECT * FROM sp_display_cooperatives(1);
```

#### 3. `sp_edit_cooperative`
Updates cooperative and all related data. Supports:
- Updating existing records
- Creating missing profile/financial records
- Replacing officers and members arrays

**Usage:**
```sql
SELECT * FROM sp_edit_cooperative(
    1,  -- coop_id
    'Updated Name',
    -- other parameters...
);
```

#### 4. `sp_delete_cooperative`
Deletes cooperative with soft or hard delete options:
- **Soft delete**: Marks records as 'rejected' (keeps data)
- **Hard delete**: Permanently removes all related records

**Usage:**
```sql
-- Soft delete
SELECT * FROM sp_delete_cooperative(1, FALSE);

-- Hard delete
SELECT * FROM sp_delete_cooperative(1, TRUE);
```

---

## OCR Service Backend

### File: `apps/core/services/ocr_service.py`

**Features:**
- Image URL processing
- File upload processing
- Base64 image processing (clipboard/screenshot)
- Error handling and response formatting

**Methods:**
- `process_image_url(image_url)` - Process remote image
- `process_image_file(file)` - Process uploaded file
- `process_base64_image(base64_data)` - Process clipboard/screenshot

**Configuration:**
Add to environment variables or Django settings:
```python
OPTIIC_API_KEY = 'your_api_key_here'  # Get from https://optiic.dev
```

### Endpoint: `/api/ocr/process/`

**Accepts:**
- File upload (multipart/form-data with 'image' field)
- URL (POST with 'url' field)
- Base64 (JSON with 'base64' field)

**Response:**
```json
{
    "success": true,
    "text": "Extracted text content...",
    "language": "en",
    "error": null
}
```

---

## OCR Assistant UI

### Features

#### 1. **Slide-Out Drawer**
- **Position**: Right side of screen
- **Width**: 350px
- **Behavior**: Push-content layout (shifts main content left)
- **Animation**: Smooth 0.3s transition

#### 2. **Activation Button**
- **Icon**: `bi-upc-scan` (scanner icon)
- **Position**: Fixed bottom-right (60x60px circular button)
- **Style**: Gradient purple background with hover effects

#### 3. **Input Methods**

**Upload Image:**
- Click upload button or upload area
- Drag & drop images onto upload zone
- Supports all image formats

**Take Screenshot:**
- Uses browser Screen Capture API
- Captures screen/window/tab
- Automatically processes captured image

**Paste from Clipboard:**
- Reads image from clipboard
- Works with copied images
- Automatic base64 conversion

**Drag & Drop:**
- Visual feedback on dragover
- Accepts image files only
- Instant processing

#### 4. **Results Display**
- Editable textarea with extracted text
- Language detection display
- Apply to form functionality
- Clear button to reset

#### 5. **Form Auto-Population**
Basic pattern matching for:
- Cooperative name
- Address
- Email
- Contact number
- CDA registration number

**Enhance the parser** in `parseAndPopulateForm()` function for your specific form fields.

---

## Installation & Setup

### 1. Apply Database Changes

```bash
# Connect to PostgreSQL
psql -U your_user -d kooptimizer

# Run migration script
\i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/apply_all_db_changes.sql

# Apply stored procedures
\i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_add_cooperative.sql
\i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_display_cooperatives.sql
\i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_edit_cooperative.sql
\i c:/Users/Noe\ Gonzales/Downloads/System/Kooptimizer/stored_procedures/sp_delete_cooperative.sql
```

### 2. Install Python Dependencies

Already installed:
- `requests` - For Optiic API calls

### 3. Configure Optiic API Key

**Option A: Environment Variable**
```bash
# Windows PowerShell
$env:OPTIIC_API_KEY = "your_api_key_here"

# Linux/Mac
export OPTIIC_API_KEY="your_api_key_here"
```

**Option B: Django Settings**
Edit `kooptimizer/settings.py`:
```python
OPTIIC_API_KEY = 'your_api_key_here'
```

**Get API Key:**
1. Visit https://optiic.dev
2. Sign up for free account
3. Copy your API key
4. Free tier available with test_api_key for testing

### 4. Run Migrations (if needed)

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start Development Server

```bash
python manage.py runserver
```

### 6. Access OCR Assistant

Navigate to: http://localhost:8000/databank/

Click the purple scanner button in bottom-right corner.

---

## Usage Guide

### Basic OCR Workflow

1. **Open OCR Assistant**
   - Click the scanner icon button (bottom-right)
   - Drawer slides in from right

2. **Process Image**
   - **Upload**: Click "Upload Image" or drag & drop
   - **Screenshot**: Click "Take Screenshot", select window
   - **Clipboard**: Copy image, click "Paste from Clipboard"

3. **Review Results**
   - Extracted text appears in textarea
   - Edit if needed
   - Check detected language

4. **Apply to Form**
   - Click "Apply to Form"
   - Review auto-populated fields
   - Adjust as needed

5. **Clear & Reset**
   - Click "Clear" to start over
   - Close drawer when done

### Customizing Form Auto-Population

Edit the `parseAndPopulateForm()` function in the template:

```javascript
function parseAndPopulateForm(text) {
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);
    
    lines.forEach(line => {
        // Add custom patterns for your form fields
        if (line.match(/your pattern here/i)) {
            const value = line.match(/your pattern here/i)[1];
            const field = document.querySelector('[name="field_name"]');
            if (field) field.value = value;
        }
    });
}
```

---

## File Structure

```
Kooptimizer/
├── migrations/
│   └── 001_update_cooperatives_schema.sql
├── stored_procedures/
│   ├── sp_add_cooperative.sql
│   ├── sp_display_cooperatives.sql
│   ├── sp_edit_cooperative.sql
│   └── sp_delete_cooperative.sql
├── apps/
│   ├── core/
│   │   └── services/
│   │       ├── ocr_service.py          # NEW: OCR service backend
│   │       └── email_service.py        # Updated with attachments
│   └── databank/
│       ├── views.py                     # Updated with OCR endpoint
│       └── urls.py                      # Added OCR route
├── templates/
│   └── databank/
│       └── databank_management.html     # Updated with OCR UI
├── kooptimizer/
│   └── settings.py                      # Added OPTIIC_API_KEY
└── apply_all_db_changes.sql            # Master migration script
```

---

## Browser Compatibility

### Fully Supported:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Features by Browser:

| Feature | Chrome | Firefox | Safari |
|---------|--------|---------|--------|
| Upload | ✅ | ✅ | ✅ |
| Drag & Drop | ✅ | ✅ | ✅ |
| Clipboard Paste | ✅ | ✅ | ⚠️ |
| Screenshot | ✅ | ⚠️ | ❌ |

**Note**: Screenshot feature requires user permission and may not work in all browsers. Upload is the most reliable method.

---

## Troubleshooting

### OCR Processing Fails

**Problem**: "OCR processing failed" error

**Solutions:**
1. Check API key is set correctly
2. Verify image format is supported (PNG, JPEG, etc.)
3. Check image size (Optiic has limits)
4. Test with `test_api_key` first

### Clipboard Access Denied

**Problem**: "Unable to access clipboard"

**Solutions:**
1. Grant clipboard permissions in browser
2. Use HTTPS (required for clipboard API)
3. Use Upload method instead

### Screenshot Not Working

**Problem**: Screenshot feature doesn't work

**Solutions:**
1. Use Chrome/Edge for best support
2. Grant screen capture permission
3. Use Upload or Clipboard instead

### Form Fields Not Populating

**Problem**: "Apply to Form" doesn't populate fields

**Solutions:**
1. Check form field `name` attributes match parser
2. Enhance `parseAndPopulateForm()` function
3. Check browser console for errors
4. Verify form fields exist on page

---

## API Limits (Optiic.dev)

### Free Tier:
- **Requests**: Limited per month (check Optiic.dev)
- **Image Size**: Check current limits
- **Rate Limiting**: May apply

### Get More:
Visit https://optiic.dev/pricing for paid plans

---

## Security Considerations

1. **API Key Protection**
   - Store in environment variables
   - Never commit to version control
   - Use different keys for dev/prod

2. **Image Upload Validation**
   - File type checking on backend
   - Size limits enforced
   - Sanitize filenames

3. **CSRF Protection**
   - All POST requests include CSRF token
   - Django middleware enabled

---

## Future Enhancements

- [ ] Advanced text parsing with NLP
- [ ] Multiple language support
- [ ] Batch image processing
- [ ] OCR result caching
- [ ] PDF document support
- [ ] Table extraction from images
- [ ] Confidence score display
- [ ] OCR history/audit trail

---

## Support & Resources

- **Optiic Documentation**: https://optiic.dev/documentation
- **Optiic NPM Package**: https://www.npmjs.com/package/optiic
- **Django Docs**: https://docs.djangoproject.com
- **Bootstrap Icons**: https://icons.getbootstrap.com

---

## License

This implementation follows the license of the Kooptimizer project.

---

**Created**: November 20, 2025  
**Version**: 1.0.0  
**Author**: GitHub Copilot
