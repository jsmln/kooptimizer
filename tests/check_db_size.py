"""
Check PostgreSQL database size and storage information
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

def get_database_size():
    """Get the size of the current database"""
    with connection.cursor() as cursor:
        # Get database name
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        
        # Get database size
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                   pg_database_size(current_database()) as db_size_bytes;
        """)
        result = cursor.fetchone()
        db_size_pretty = result[0]
        db_size_bytes = result[1]
        
        # Get table sizes
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        """)
        tables = cursor.fetchall()
        
        # Get attachment storage info
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(CASE WHEN attachment IS NOT NULL THEN 1 END) as messages_with_attachments,
                pg_size_pretty(SUM(COALESCE(attachment_size, 0))) as total_attachment_size,
                SUM(COALESCE(attachment_size, 0)) as total_attachment_bytes
            FROM messages;
        """)
        msg_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_announcements,
                COUNT(CASE WHEN attachment IS NOT NULL THEN 1 END) as announcements_with_attachments,
                pg_size_pretty(SUM(COALESCE(attachment_size, 0))) as total_attachment_size,
                SUM(COALESCE(attachment_size, 0)) as total_attachment_bytes
            FROM announcements;
        """)
        ann_stats = cursor.fetchone()
        
        print("\n" + "="*70)
        print(f"DATABASE: {db_name}")
        print("="*70)
        print(f"\nTotal Database Size: {db_size_pretty} ({db_size_bytes:,} bytes)")
        print(f"\n{'='*70}")
        print("TOP 10 LARGEST TABLES:")
        print(f"{'='*70}")
        print(f"{'Schema':<15} {'Table':<30} {'Size':<15}")
        print("-"*70)
        for schema, table, size, size_bytes in tables:
            print(f"{schema:<15} {table:<30} {size:<15}")
        
        print(f"\n{'='*70}")
        print("MESSAGE ATTACHMENTS:")
        print(f"{'='*70}")
        print(f"Total Messages: {msg_stats[0]:,}")
        print(f"Messages with Attachments: {msg_stats[1]:,}")
        print(f"Total Attachment Storage: {msg_stats[2]} ({msg_stats[3]:,} bytes)")
        
        print(f"\n{'='*70}")
        print("ANNOUNCEMENT ATTACHMENTS:")
        print(f"{'='*70}")
        print(f"Total Announcements: {ann_stats[0]:,}")
        print(f"Announcements with Attachments: {ann_stats[1]:,}")
        print(f"Total Attachment Storage: {ann_stats[2]} ({ann_stats[3]:,} bytes)")
        
        # Calculate storage limits
        max_msg_attachment = 4 * 1024 * 1024  # 4MB per message
        max_ann_attachment = 25 * 1024 * 1024  # 25MB per announcement
        
        total_attachment_bytes = (msg_stats[3] or 0) + (ann_stats[3] or 0)
        
        print(f"\n{'='*70}")
        print("STORAGE SUMMARY:")
        print(f"{'='*70}")
        print(f"Total Attachment Storage: {total_attachment_bytes / (1024*1024):.2f} MB")
        print(f"Max per Message: 4 MB")
        print(f"Max per Announcement: 25 MB")
        
        # Try to get disk space info (this may not work on all systems)
        try:
            cursor.execute("""
                SELECT 
                    pg_size_pretty(pg_tablespace_size('pg_default')) as tablespace_size;
            """)
            ts_size = cursor.fetchone()[0]
            print(f"Default Tablespace Size: {ts_size}")
        except Exception as e:
            print(f"Could not retrieve tablespace info: {e}")
        
        print(f"\n{'='*70}\n")

if __name__ == '__main__':
    get_database_size()
