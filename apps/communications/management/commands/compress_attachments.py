"""
Django management command to compress existing attachments in the database.

This command will:
1. Find all messages with attachments
2. Apply compression to each attachment
3. Update the database with compressed versions
4. Report storage savings

Usage:
    python manage.py compress_attachments
    python manage.py compress_attachments --dry-run  # Preview without saving
    python manage.py compress_attachments --limit 100  # Process only first 100
    python manage.py compress_attachments --batch-size 50  # Process in batches
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.communications.models import Message, Announcement
from apps.communications.utils import process_attachment
from io import BytesIO
import sys


class MockUploadedFile:
    """Mock Django UploadedFile for processing existing attachments."""
    def __init__(self, data, name, content_type):
        self.data = data
        self.name = name
        self.content_type = content_type
        self._read = False
    
    def read(self):
        if self._read:
            return self.data
        self._read = True
        return self.data


class Command(BaseCommand):
    help = 'Compress existing attachments in the database to save storage space'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview compression results without saving to database',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of attachments to process',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of records to process in each batch (default: 10)',
        )
        parser.add_argument(
            '--messages-only',
            action='store_true',
            help='Process only message attachments',
        )
        parser.add_argument(
            '--announcements-only',
            action='store_true',
            help='Process only announcement attachments',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        batch_size = options['batch_size']
        messages_only = options['messages_only']
        announcements_only = options['announcements_only']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Attachment Compression Tool'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved\n'))

        total_original_size = 0
        total_compressed_size = 0
        total_processed = 0
        total_errors = 0
        total_skipped = 0

        # Process Messages
        if not announcements_only:
            self.stdout.write(self.style.HTTP_INFO('\n📨 Processing Message Attachments...'))
            msg_stats = self._process_messages(dry_run, limit, batch_size)
            total_original_size += msg_stats['original_size']
            total_compressed_size += msg_stats['compressed_size']
            total_processed += msg_stats['processed']
            total_errors += msg_stats['errors']
            total_skipped += msg_stats['skipped']

        # Process Announcements
        if not messages_only:
            self.stdout.write(self.style.HTTP_INFO('\n📢 Processing Announcement Attachments...'))
            ann_stats = self._process_announcements(dry_run, limit, batch_size)
            total_original_size += ann_stats['original_size']
            total_compressed_size += ann_stats['compressed_size']
            total_processed += ann_stats['processed']
            total_errors += ann_stats['errors']
            total_skipped += ann_stats['skipped']

        # Final Report
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('COMPRESSION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'✅ Processed: {total_processed}')
        self.stdout.write(f'⏭️  Skipped: {total_skipped}')
        self.stdout.write(f'❌ Errors: {total_errors}')
        
        if total_original_size > 0:
            savings = total_original_size - total_compressed_size
            savings_percent = (savings / total_original_size) * 100
            
            self.stdout.write(f'\n📊 Original Size: {self._format_size(total_original_size)}')
            self.stdout.write(f'📊 Compressed Size: {self._format_size(total_compressed_size)}')
            self.stdout.write(self.style.SUCCESS(
                f'💾 Storage Saved: {self._format_size(savings)} ({savings_percent:.1f}%)'
            ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN - No changes were saved to database'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All changes saved to database'))

    def _process_messages(self, dry_run, limit, batch_size):
        """Process message attachments."""
        stats = {
            'original_size': 0,
            'compressed_size': 0,
            'processed': 0,
            'errors': 0,
            'skipped': 0
        }

        # Get messages with attachments
        messages = Message.objects.filter(attachment__isnull=False).exclude(attachment=b'')
        
        if limit:
            messages = messages[:limit]
        
        total = messages.count()
        self.stdout.write(f'Found {total} messages with attachments\n')

        for i, msg in enumerate(messages, 1):
            try:
                # Progress indicator
                if i % batch_size == 0 or i == total:
                    self.stdout.write(f'Progress: {i}/{total}', ending='\r')
                    self.stdout.flush()

                # Get original data
                original_data = bytes(msg.attachment) if isinstance(msg.attachment, memoryview) else msg.attachment
                original_size = len(original_data)
                
                if original_size == 0:
                    stats['skipped'] += 1
                    continue

                # Create mock file object
                mock_file = MockUploadedFile(
                    original_data,
                    msg.attachment_filename or 'attachment',
                    msg.attachment_content_type or 'application/octet-stream'
                )

                # Compress
                compressed_data, content_type, filename, compressed_size = process_attachment(
                    mock_file,
                    msg.attachment_filename or 'attachment'
                )

                # Update stats
                stats['original_size'] += original_size
                stats['compressed_size'] += compressed_size
                stats['processed'] += 1

                # Show individual result
                savings = original_size - compressed_size
                if savings > 0:
                    savings_percent = (savings / original_size) * 100
                    self.stdout.write(
                        f'  Message {msg.message_id}: '
                        f'{self._format_size(original_size)} → {self._format_size(compressed_size)} '
                        f'({savings_percent:.1f}% saved)'
                    )

                # Save to database (if not dry run)
                if not dry_run:
                    msg.attachment = compressed_data
                    msg.attachment_filename = filename
                    msg.attachment_content_type = content_type
                    msg.attachment_size = compressed_size
                    msg.save(update_fields=['attachment', 'attachment_filename', 
                                           'attachment_content_type', 'attachment_size'])

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(f'  Error processing message {msg.message_id}: {str(e)}')
                )

        self.stdout.write('')  # New line after progress
        return stats

    def _process_announcements(self, dry_run, limit, batch_size):
        """Process announcement attachments."""
        stats = {
            'original_size': 0,
            'compressed_size': 0,
            'processed': 0,
            'errors': 0,
            'skipped': 0
        }

        # Get announcements with attachments
        announcements = Announcement.objects.filter(attachment__isnull=False).exclude(attachment=b'')
        
        if limit:
            announcements = announcements[:limit]
        
        total = announcements.count()
        self.stdout.write(f'Found {total} announcements with attachments\n')

        for i, ann in enumerate(announcements, 1):
            try:
                # Progress indicator
                if i % batch_size == 0 or i == total:
                    self.stdout.write(f'Progress: {i}/{total}', ending='\r')
                    self.stdout.flush()

                # Get original data
                original_data = bytes(ann.attachment) if isinstance(ann.attachment, memoryview) else ann.attachment
                original_size = len(original_data)
                
                if original_size == 0:
                    stats['skipped'] += 1
                    continue

                # Create mock file object
                mock_file = MockUploadedFile(
                    original_data,
                    ann.attachment_filename or 'attachment',
                    ann.attachment_content_type or 'application/octet-stream'
                )

                # Compress
                compressed_data, content_type, filename, compressed_size = process_attachment(
                    mock_file,
                    ann.attachment_filename or 'attachment'
                )

                # Update stats
                stats['original_size'] += original_size
                stats['compressed_size'] += compressed_size
                stats['processed'] += 1

                # Show individual result
                savings = original_size - compressed_size
                if savings > 0:
                    savings_percent = (savings / original_size) * 100
                    self.stdout.write(
                        f'  Announcement {ann.announcement_id}: '
                        f'{self._format_size(original_size)} → {self._format_size(compressed_size)} '
                        f'({savings_percent:.1f}% saved)'
                    )

                # Save to database (if not dry run)
                if not dry_run:
                    ann.attachment = compressed_data
                    ann.attachment_filename = filename
                    ann.attachment_content_type = content_type
                    ann.attachment_size = compressed_size
                    ann.save(update_fields=['attachment', 'attachment_filename', 
                                           'attachment_content_type', 'attachment_size'])

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(f'  Error processing announcement {ann.announcement_id}: {str(e)}')
                )

        self.stdout.write('')  # New line after progress
        return stats

    def _format_size(self, bytes_size):
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f'{bytes_size:.2f} {unit}'
            bytes_size /= 1024.0
        return f'{bytes_size:.2f} TB'
