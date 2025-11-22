#!/usr/bin/env python
"""
Announcement Attachments Migration Script
==========================================
This script migrates announcement attachments from the old single-blob structure
to the new individual attachments table structure.

Usage:
    python database_updates/apply_announcement_attachments_migration.py

What it does:
1. Creates the announcement_attachments table
2. Migrates existing attachment data
3. Verifies the migration
4. Provides rollback information
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection, transaction
from apps.communications.models import Announcement, AnnouncementAttachment
from apps.users.models import User


def run_sql_file(filename):
    """Execute SQL from a file, handling multiple statements properly"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split into statements, handling DO blocks specially
    statements = []
    current_statement = []
    in_do_block = False
    
    for line in sql_content.split('\n'):
        stripped = line.strip()
        
        # Track DO blocks
        if stripped.startswith('DO $$') or stripped.startswith('DO $'):
            in_do_block = True
            current_statement.append(line)
        elif in_do_block:
            current_statement.append(line)
            if stripped.endswith('$$;') or stripped.endswith('$;'):
                in_do_block = False
                statements.append('\n'.join(current_statement))
                current_statement = []
        elif stripped.startswith('--') or stripped == '':
            # Skip comments and empty lines unless in DO block
            continue
        elif stripped.endswith(';'):
            current_statement.append(line)
            statements.append('\n'.join(current_statement))
            current_statement = []
        else:
            current_statement.append(line)
    
    # Execute each statement
    with connection.cursor() as cursor:
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"  ✓ Executed statement {i+1}/{len(statements)}")
                except Exception as e:
                    print(f"  ✗ Error in statement {i+1}: {str(e)}")
                    raise
    
    print(f"✓ Successfully executed all statements from {filename}")


def verify_migration():
    """Verify the migration was successful"""
    with connection.cursor() as cursor:
        # Check old structure
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcements 
            WHERE attachment IS NOT NULL 
              AND attachment_filename IS NOT NULL
        """)
        old_count = cursor.fetchone()[0]
        
        # Check new structure
        cursor.execute("SELECT COUNT(*) FROM announcement_attachments")
        new_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT announcement_id) FROM announcement_attachments")
        announcements_with_attachments = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("MIGRATION VERIFICATION")
        print("="*60)
        print(f"Announcements with old attachments: {old_count}")
        print(f"New attachment records created:     {new_count}")
        print(f"Announcements with new attachments: {announcements_with_attachments}")
        print("="*60)
        
        if old_count == announcements_with_attachments or old_count == 0:
            print("✓ Migration appears successful!")
            return True
        else:
            print("⚠ Warning: Counts don't match. Please review.")
            return False


def test_attachment_access():
    """Test that we can access attachments through the new model"""
    print("\n" + "="*60)
    print("TESTING ATTACHMENT ACCESS")
    print("="*60)
    
    # Get an announcement with attachments
    ann_with_attachments = Announcement.objects.filter(
        attachments__isnull=False
    ).first()
    
    if ann_with_attachments:
        print(f"Testing announcement: {ann_with_attachments.title}")
        print(f"Attachments count: {ann_with_attachments.attachments.count()}")
        
        for idx, attachment in enumerate(ann_with_attachments.attachments.all(), 1):
            print(f"  {idx}. {attachment.original_filename} ({attachment.file_size} bytes)")
        
        print("✓ Attachment access working correctly!")
    else:
        print("ℹ No announcements with attachments found in database")
    
    print("="*60)


def main():
    print("\n" + "="*60)
    print("ANNOUNCEMENT ATTACHMENTS MIGRATION")
    print("="*60)
    print("\nThis will:")
    print("1. Create announcement_attachments table")
    print("2. Migrate existing attachment data")
    print("3. Preserve old columns for backward compatibility")
    print("\n⚠ IMPORTANT: Backup your database before proceeding!")
    
    response = input("\nContinue with migration? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Migration cancelled.")
        return
    
    try:
        with transaction.atomic():
            print("\n🔄 Starting migration...")
            
            # Run the SQL migration
            run_sql_file('migrate_announcement_attachments.sql')
            
            print("✓ Migration SQL executed successfully")
            
            # Verify the migration
            if not verify_migration():
                response = input("\nWarning detected. Continue anyway? (yes/no): ").strip().lower()
                if response != 'yes':
                    raise Exception("Migration verification failed - rolling back")
            
            # Test attachment access
            test_attachment_access()
            
            print("\n" + "="*60)
            print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. Test the announcement attachment functionality")
            print("2. Update your views to use the new AnnouncementAttachment model")
            print("3. After thorough testing, you can drop old attachment columns")
            print("\nTo drop old columns (AFTER TESTING), run:")
            print("  ALTER TABLE announcements DROP COLUMN attachment;")
            print("  ALTER TABLE announcements DROP COLUMN attachment_filename;")
            print("  ALTER TABLE announcements DROP COLUMN attachment_content_type;")
            print("  ALTER TABLE announcements DROP COLUMN attachment_size;")
            print("="*60 + "\n")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Changes have been rolled back.")
        raise


if __name__ == '__main__':
    main()
