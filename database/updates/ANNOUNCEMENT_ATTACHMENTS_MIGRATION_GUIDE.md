# Announcement Attachments Migration Guide

## Overview
This guide documents the migration from combined attachment storage (single BLOB) to individual attachment records in a separate table.

## Changes Summary

### Database Changes
- **New Table**: `announcement_attachments` - stores individual attachment records
- **Updated Stored Procedure**: `sp_get_announcement_details` - returns individual attachment data
- **Legacy Fields Preserved**: Old attachment columns remain for backward compatibility

### Backend Changes
- **New Model**: `AnnouncementAttachment` model added to `apps/communications/models.py`
- **New Utility Module**: `apps/communications/attachment_utils.py` - handles attachment operations
- **Updated Views**:
  - `handle_announcement` - uses new save/update attachment functions
  - `download_announcement_attachment` - supports both old and new structures
  - `convert_announcement_attachment_to_pdf` - supports both old and new structures

### Frontend Changes
- **Advanced Preview Modal**: Added to `announcement_form.html` with PDF.js support
- **File Preview**: Supports PDF, DOCX, XLSX, PPTX, images, TXT, CSV
- **PDF Conversion**: Client can convert documents to PDF for preview

## Migration Steps

### Step 1: Backup Database (Recommended but Optional)

**Option A: Using pg_dump (if PostgreSQL tools are in PATH)**
```bash
# Create a backup before migration
pg_dump -U your_username -d kooptimizer_db > backup_before_migration.sql
```

**Option B: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Right-click on your database
3. Select "Backup..."
4. Choose a location and click "Backup"

**Option C: Skip backup and proceed**
- The migration script uses transactions and will rollback on errors
- However, a backup is still recommended for production systems
- For development/testing, you can proceed without backup

### Step 2: Run Database Migration
```bash
# Navigate to the project directory
cd "c:\Users\Noe Gonzales\Downloads\System\Kooptimizer"

# Run the migration script
python database_updates/apply_announcement_attachments_migration.py
```

The migration script will:
1. Create the `announcement_attachments` table
2. Migrate existing attachment data
3. Verify data integrity
4. Test ORM access

### Step 3: Update Stored Procedure
```bash
# Apply the updated stored procedure
psql -U your_username -d kooptimizer_db -f database_updates/update_sp_get_announcement_details_v2.sql
```

### Step 4: Test the System

#### Test Upload (New Structure)
1. Go to Announcements page
2. Create a new announcement
3. Upload multiple files
4. Verify files are saved individually in `announcement_attachments` table

#### Test Preview
1. Open an announcement with attachments
2. Click Preview button on each file type:
   - PDF files should open directly
   - DOCX/XLSX/PPTX should convert to PDF
   - Images should display in image viewer
3. Test zoom, rotation, page navigation (for PDFs)

#### Test Download
1. Download individual files
2. Verify correct file is downloaded
3. Test "Download as PDF" for convertible documents

#### Test Legacy Data
1. Open old announcements (created before migration)
2. Verify attachments still display correctly
3. Test preview/download on legacy attachments

## Database Schema

### New Table Structure
```sql
CREATE TABLE announcement_attachments (
    attachment_id SERIAL PRIMARY KEY,
    announcement_id INTEGER NOT NULL REFERENCES announcements(announcement_id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size INTEGER,
    file_data BYTEA NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    display_order INTEGER DEFAULT 0
);

CREATE INDEX idx_announcement_attachments_announcement 
    ON announcement_attachments(announcement_id);
CREATE INDEX idx_announcement_attachments_uploaded_at 
    ON announcement_attachments(uploaded_at);
```

### Model Relationships
```python
# One-to-Many relationship
Announcement -> AnnouncementAttachment (attachments)
User -> AnnouncementAttachment (uploaded_by)
```

## API Endpoints

### Download Attachment
**Old Format (Legacy):**
```
GET /communications/api/announcement/{announcement_id}/attachment/
```

**New Format (Individual File):**
```
GET /communications/api/announcement/{announcement_id}/attachment/?attachment_id={attachment_id}
```

**Preview Mode:**
```
GET /communications/api/announcement/{announcement_id}/attachment/?attachment_id={attachment_id}&preview=true
```

**Convert to PDF:**
```
GET /communications/api/announcement/{announcement_id}/attachment/?attachment_id={attachment_id}&format=pdf
```

### Convert to PDF (POST)
**Old Format:**
```
POST /communications/api/announcement/{announcement_id}/attachment/convert-pdf/
```

**New Format:**
```
POST /communications/api/announcement/{announcement_id}/attachment/convert-pdf/
Body: {"attachment_id": 123}
```

## Utility Functions (attachment_utils.py)

### save_announcement_attachments()
Saves multiple uploaded files as individual records.
```python
success, message, count = save_announcement_attachments(
    announcement_id=123,
    uploaded_files=request.FILES.getlist('attachments'),
    user_id=1
)
```

### update_announcement_attachments()
Updates announcement attachments.
```python
success, message, count = update_announcement_attachments(
    announcement_id=123,
    uploaded_files=request.FILES.getlist('attachments'),
    user_id=1,
    keep_existing=True  # True to append, False to replace
)
```

### delete_announcement_attachment()
Deletes a specific attachment.
```python
success, message = delete_announcement_attachment(attachment_id=456)
```

### get_announcement_attachments_info()
Gets attachment metadata without binary data.
```python
attachments = get_announcement_attachments_info(announcement_id=123)
# Returns list of dicts with: attachment_id, filename, content_type, file_size, etc.
```

### migrate_legacy_attachment()
One-time migration helper for legacy data.
```python
success, message = migrate_legacy_attachment(
    announcement_id=123,
    user_id=1
)
```

## Backward Compatibility

### Legacy Attachments
- Old announcements with combined attachments will still work
- Download/preview views check for new structure first, fall back to legacy
- Frontend displays attachments from both sources
- No data loss during transition

### Gradual Migration
- New announcements automatically use new structure
- Old announcements remain on legacy structure
- Optional: Use `migrate_legacy_attachment()` to convert specific announcements
- Optional: Bulk migrate all legacy attachments (run migration script again)

## Rollback Plan

If issues occur during migration:

### Step 1: Restore Database
```bash
psql -U your_username -d kooptimizer_db < backup_before_migration.sql
```

### Step 2: Revert Code Changes
```bash
git checkout HEAD -- apps/communications/models.py
git checkout HEAD -- apps/communications/views.py
git checkout HEAD -- templates/communications/announcement_form.html
# Remove new file
rm apps/communications/attachment_utils.py
```

### Step 3: Restart Application
```bash
# Restart Django server
```

## Verification Queries

### Check Migration Success
```sql
-- Count records in new table
SELECT COUNT(*) FROM announcement_attachments;

-- Compare counts
SELECT 
    (SELECT COUNT(*) FROM announcements WHERE attachment IS NOT NULL) as legacy_count,
    (SELECT COUNT(DISTINCT announcement_id) FROM announcement_attachments) as migrated_count;

-- Check for orphaned attachments
SELECT aa.attachment_id, aa.announcement_id 
FROM announcement_attachments aa
LEFT JOIN announcements a ON aa.announcement_id = a.announcement_id
WHERE a.announcement_id IS NULL;
```

### Check Stored Procedure
```sql
-- Test stored procedure
SELECT * FROM sp_get_announcement_details(1);
-- Should return attachments_json field with JSON array
```

## Performance Considerations

### Indexes
- `idx_announcement_attachments_announcement` - Fast lookup by announcement
- `idx_announcement_attachments_uploaded_at` - For date-based queries

### Query Optimization
- Use `select_related('announcement')` when querying attachments
- Use `prefetch_related('attachments')` when querying announcements
- Avoid loading `file_data` field unless necessary

Example:
```python
# Good: Only load metadata
attachments = AnnouncementAttachment.objects.filter(
    announcement_id=123
).values('attachment_id', 'filename', 'content_type', 'file_size')

# Bad: Loads all binary data
attachments = AnnouncementAttachment.objects.filter(announcement_id=123)
```

## Troubleshooting

### Issue: Preview not working
**Solution:** Check that PDF.js library is loading:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
```

### Issue: Download fails with "Attachment not found"
**Solution:** Check if `attachment_id` parameter is being sent:
```javascript
// Ensure URL includes attachment_id
const url = `/communications/api/announcement/${announcementId}/attachment/?attachment_id=${attachmentId}`;
```

### Issue: Old attachments not displaying
**Solution:** Verify legacy fallback logic in views:
```python
if attachment_id:
    # New structure
    attachment = AnnouncementAttachment.objects.get(...)
else:
    # Legacy structure
    if announcement.attachment:
        # Handle legacy data
```

### Issue: Migration script fails
**Solution:** Check database permissions:
```sql
-- Ensure user has CREATE TABLE permission
GRANT CREATE ON SCHEMA public TO your_username;
```

## Future Enhancements

1. **Cloud Storage**: Move from bytea to cloud storage (S3, Azure Blob)
   - Keep `announcement_attachments` table structure
   - Replace `file_data BYTEA` with `storage_url VARCHAR`
   - Update utility functions to use cloud SDK

2. **Attachment Versions**: Track file versions
   - Add `version INTEGER` column
   - Add `replaced_by INTEGER` foreign key
   - Implement version history

3. **Virus Scanning**: Scan uploads
   - Add `scan_status VARCHAR` column
   - Integrate ClamAV or similar
   - Block downloads if infected

4. **Attachment Sharing**: Share links
   - Add `share_token VARCHAR` column
   - Generate secure URLs
   - Track access logs

## Support

For issues or questions:
1. Check this guide first
2. Review migration logs
3. Check database error logs
4. Contact development team

## Change Log

- **v1.0** (Current): Initial migration from combined to individual attachments
- Added `announcement_attachments` table
- Updated stored procedures
- Added utility functions
- Added advanced preview modal
