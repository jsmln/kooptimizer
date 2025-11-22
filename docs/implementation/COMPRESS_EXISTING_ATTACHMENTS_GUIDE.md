# Compress Existing Attachments - Usage Guide

## Overview
The `compress_attachments` management command allows you to compress attachments that are already saved in the database, helping you reclaim storage space.

## Basic Usage

### 1. Preview Mode (Dry Run)
See what would be compressed without making changes:
```bash
python manage.py compress_attachments --dry-run
```

### 2. Compress All Attachments
Compress all message and announcement attachments:
```bash
python manage.py compress_attachments
```

### 3. Compress Messages Only
```bash
python manage.py compress_attachments --messages-only
```

### 4. Compress Announcements Only
```bash
python manage.py compress_attachments --announcements-only
```

## Advanced Options

### Process Limited Number
Compress only first 100 attachments:
```bash
python manage.py compress_attachments --limit 100
```

### Adjust Batch Size
Process 50 records at a time (default is 10):
```bash
python manage.py compress_attachments --batch-size 50
```

### Combined Options
Dry run for first 50 messages with larger batches:
```bash
python manage.py compress_attachments --dry-run --messages-only --limit 50 --batch-size 25
```

## Output Example

```
======================================================================
Attachment Compression Tool
======================================================================

📨 Processing Message Attachments...
Found 150 messages with attachments

  Message 1: 3.45 MB → 1.12 MB (67.5% saved)
  Message 2: 2.89 MB → 890.23 KB (69.2% saved)
  Message 3: 1.23 MB → 456.78 KB (62.9% saved)
  ...
Progress: 150/150

📢 Processing Announcement Attachments...
Found 45 announcements with attachments

  Announcement 1: 5.67 MB → 2.34 MB (58.7% saved)
  Announcement 2: 1.89 MB → 678.90 KB (64.1% saved)
  ...
Progress: 45/45

======================================================================
COMPRESSION SUMMARY
======================================================================
✅ Processed: 195
⏭️  Skipped: 0
❌ Errors: 0

📊 Original Size: 456.78 MB
📊 Compressed Size: 178.34 MB
💾 Storage Saved: 278.44 MB (60.9%)

✅ All changes saved to database
```

## What Gets Compressed?

### Images
- Resized to max 1920px
- Converted to optimized JPEG (85% quality) or PNG
- **Typical reduction**: 60-80%

### PDFs
- Content stream compression
- **Typical reduction**: 10-30%

### Office Documents
- Word, Excel, PowerPoint
- Gzipped if beneficial (>10% reduction)
- **Typical reduction**: 0-20%

### Text Files
- TXT, CSV, JSON, XML
- Gzip compression (level 9)
- **Typical reduction**: 70-90%

### Other Files
- Gzip compression if beneficial
- **Typical reduction**: 30-70%

### Already Compressed Files
- ZIP, RAR, videos, audio
- Left as-is (no benefit from compression)
- **Reduction**: 0%

## Safety Features

1. **Dry Run Mode**: Preview changes without saving
2. **Batch Processing**: Processes records in small batches to avoid memory issues
3. **Error Handling**: Continues processing even if some files fail
4. **Progress Tracking**: Real-time progress updates
5. **Detailed Reporting**: Shows individual and total savings

## Recommended Workflow

### First Time Compression

1. **Preview** what will happen:
   ```bash
   python manage.py compress_attachments --dry-run
   ```

2. **Test** on a small batch first:
   ```bash
   python manage.py compress_attachments --limit 10
   ```

3. **Verify** results in database, then compress all:
   ```bash
   python manage.py compress_attachments
   ```

### Regular Maintenance

Run monthly to catch any attachments uploaded before compression was enabled:
```bash
python manage.py compress_attachments
```

## Performance Considerations

### Processing Speed
- **Images**: 100-500ms per file
- **PDFs**: 50-200ms per file
- **Other files**: 10-100ms per file

### Memory Usage
- Batch size of 10 (default): ~50-100 MB RAM
- Batch size of 50: ~200-400 MB RAM
- Batch size of 100: ~400-800 MB RAM

### Recommended Settings
- **Small database** (<1000 attachments): Default settings
- **Medium database** (1000-10,000): `--batch-size 25`
- **Large database** (>10,000): `--batch-size 10 --limit 1000` then run multiple times

## Troubleshooting

### Command Not Found
Make sure you're in the project directory with virtual environment activated:
```bash
cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"
.venv\Scripts\Activate.ps1
python manage.py compress_attachments --dry-run
```

### Out of Memory
Reduce batch size:
```bash
python manage.py compress_attachments --batch-size 5
```

### Some Files Error
The command will continue processing. Check the error messages and:
- Verify those files aren't corrupted in database
- Check file types are supported
- Review error details in output

### No Savings Shown
This is normal for:
- Already compressed files (ZIP, videos)
- Very small files (<100 KB)
- Office documents (already compressed internally)

## Monitoring Results

### Check Database Size (PostgreSQL)
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('communications_message')) as messages_size,
    pg_size_pretty(pg_total_relation_size('communications_announcement')) as announcements_size;
```

### Count Attachments
```sql
SELECT 
    COUNT(*) as total_messages_with_attachments,
    pg_size_pretty(SUM(attachment_size)) as total_size
FROM communications_message 
WHERE attachment IS NOT NULL AND attachment != '';
```

## Automation (Optional)

### Windows Task Scheduler
Create a batch file `compress_attachments.bat`:
```batch
@echo off
cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"
call .venv\Scripts\Activate.ps1
python manage.py compress_attachments
```

Schedule to run monthly via Task Scheduler.

### Cron Job (Linux)
```bash
0 2 1 * * cd /path/to/Kooptimizer && source .venv/bin/activate && python manage.py compress_attachments
```

## Notes

- ✅ Safe to run multiple times (already compressed files won't be recompressed)
- ✅ No downtime required
- ✅ Can be stopped and resumed (processes one record at a time)
- ✅ Works on production databases
- ⚠️ Large databases may take several hours
- ⚠️ Backup database before first run (best practice)
