"""
Utility functions for handling announcement attachments
using the new AnnouncementAttachment model.
"""

from .models import AnnouncementAttachment, Announcement
from .utils import process_attachment
from django.db import transaction


def save_announcement_attachments(announcement_id, uploaded_files, user_id=None):
    """
    Save multiple attachments for an announcement.
    
    Args:
        announcement_id: ID of the announcement
        uploaded_files: List of uploaded file objects from request.FILES
        user_id: ID of the user uploading the files
    
    Returns:
        tuple: (success: bool, message: str, attachments_count: int)
    """
    if not uploaded_files:
        return True, "No attachments to save", 0
    
    try:
        announcement = Announcement.objects.get(announcement_id=announcement_id)
    except Announcement.DoesNotExist:
        return False, "Announcement not found", 0
    
    attachments_created = []
    
    try:
        with transaction.atomic():
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    # Process the file (compression, validation, etc.)
                    file_data, content_type, final_filename, file_size = process_attachment(
                        uploaded_file,
                        uploaded_file.name
                    )
                    
                    # Create attachment record
                    attachment = AnnouncementAttachment.objects.create(
                        announcement=announcement,
                        filename=final_filename,
                        original_filename=uploaded_file.name,
                        content_type=content_type,
                        file_size=file_size,
                        file_data=file_data,
                        uploaded_by_id=user_id,
                        display_order=idx
                    )
                    
                    attachments_created.append(attachment)
                    
                except ValueError as ve:
                    # Rollback will happen automatically
                    return False, str(ve), 0
                except Exception as e:
                    return False, f"Error processing {uploaded_file.name}: {str(e)}", 0
            
            return True, f"Successfully saved {len(attachments_created)} attachment(s)", len(attachments_created)
            
    except Exception as e:
        return False, f"Transaction error: {str(e)}", 0


def update_announcement_attachments(announcement_id, uploaded_files, user_id=None, keep_existing=False):
    """
    Update attachments for an announcement.
    
    Args:
        announcement_id: ID of the announcement
        uploaded_files: List of uploaded file objects from request.FILES
        user_id: ID of the user uploading the files
        keep_existing: If True, append to existing attachments. If False, replace all.
    
    Returns:
        tuple: (success: bool, message: str, attachments_count: int)
    """
    try:
        announcement = Announcement.objects.get(announcement_id=announcement_id)
    except Announcement.DoesNotExist:
        return False, "Announcement not found", 0
    
    try:
        with transaction.atomic():
            # Delete existing attachments if not keeping them
            if not keep_existing:
                announcement.attachments.all().delete()
            
            # Save new attachments
            if uploaded_files:
                success, message, count = save_announcement_attachments(
                    announcement_id,
                    uploaded_files,
                    user_id
                )
                return success, message, count
            else:
                return True, "Existing attachments removed", 0
                
    except Exception as e:
        return False, f"Error updating attachments: {str(e)}", 0


def delete_announcement_attachment(attachment_id, user_id=None):
    """
    Delete a specific attachment.
    
    Args:
        attachment_id: ID of the attachment to delete
        user_id: ID of the user requesting deletion (for permission checks)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        attachment = AnnouncementAttachment.objects.get(attachment_id=attachment_id)
        attachment.delete()
        return True, "Attachment deleted successfully"
    except AnnouncementAttachment.DoesNotExist:
        return False, "Attachment not found"
    except Exception as e:
        return False, f"Error deleting attachment: {str(e)}"


def get_announcement_attachments_info(announcement_id):
    """
    Get information about all attachments for an announcement.
    
    Args:
        announcement_id: ID of the announcement
    
    Returns:
        dict: Information about attachments including count, total size, and file list
    """
    try:
        announcement = Announcement.objects.get(announcement_id=announcement_id)
        attachments = announcement.attachments.all().order_by('display_order', 'attachment_id')
        
        total_size = sum(att.file_size for att in attachments)
        
        files_info = [
            {
                'attachment_id': att.attachment_id,
                'filename': att.original_filename,
                'content_type': att.content_type,
                'file_size': att.file_size,
                'uploaded_at': att.uploaded_at.isoformat() if att.uploaded_at else None,
                'display_order': att.display_order
            }
            for att in attachments
        ]
        
        return {
            'has_attachments': len(files_info) > 0,
            'attachment_count': len(files_info),
            'total_size': total_size,
            'files': files_info
        }
        
    except Announcement.DoesNotExist:
        return {
            'has_attachments': False,
            'attachment_count': 0,
            'total_size': 0,
            'files': []
        }


def migrate_legacy_attachment(announcement_id):
    """
    Migrate a legacy combined attachment to individual attachments.
    Used for announcements that still have data in the old format.
    
    Args:
        announcement_id: ID of the announcement
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        announcement = Announcement.objects.get(announcement_id=announcement_id)
        
        # Check if there's legacy data
        if not announcement.attachment or not announcement.attachment_filename:
            return False, "No legacy attachment data found"
        
        # Check if already migrated
        if announcement.attachments.exists():
            return False, "Attachments already migrated"
        
        # Parse filenames
        filenames = [f.strip() for f in announcement.attachment_filename.split(';') if f.strip()]
        
        with transaction.atomic():
            if len(filenames) == 1:
                # Single file - can migrate properly
                attachment = AnnouncementAttachment.objects.create(
                    announcement=announcement,
                    filename=filenames[0],
                    original_filename=filenames[0],
                    content_type=announcement.attachment_content_type or 'application/octet-stream',
                    file_size=announcement.attachment_size or len(announcement.attachment),
                    file_data=announcement.attachment,
                    display_order=0
                )
                return True, f"Migrated 1 attachment: {filenames[0]}"
            else:
                # Multiple files were combined - create a combined record
                attachment = AnnouncementAttachment.objects.create(
                    announcement=announcement,
                    filename=announcement.attachment_filename,
                    original_filename=announcement.attachment_filename,
                    content_type='application/mixed',
                    file_size=announcement.attachment_size or len(announcement.attachment),
                    file_data=announcement.attachment,
                    display_order=0
                )
                return True, f"Migrated combined attachment with {len(filenames)} files"
                
    except Announcement.DoesNotExist:
        return False, "Announcement not found"
    except Exception as e:
        return False, f"Migration error: {str(e)}"
