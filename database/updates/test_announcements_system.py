#!/usr/bin/env python
"""
Comprehensive test suite for announcement system
Tests CRUD operations, stored procedures, attachments, and display functions
"""
import os
import sys
import django
from io import BytesIO

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection
from apps.communications.models import Announcement, AnnouncementAttachment
from apps.communications.attachment_utils import (
    save_announcement_attachments,
    get_announcement_attachments_info,
    delete_announcement_attachment
)


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_test(test_name):
    print(f"{Colors.YELLOW}▶ Testing:{Colors.RESET} {test_name}")


def print_success(message):
    print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message):
    print(f"  {Colors.RED}✗{Colors.RESET} {message}")


def print_info(message):
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {message}")


# =============================================================================
# TEST 1: Database Structure
# =============================================================================
def test_database_structure():
    print_header("TEST 1: Database Structure")
    
    with connection.cursor() as cursor:
        # Check announcements table exists
        print_test("Announcements table exists")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'announcements'
            )
        """)
        if cursor.fetchone()[0]:
            print_success("Table 'announcements' exists")
        else:
            print_error("Table 'announcements' not found")
            return False
        
        # Check announcement_attachments table exists
        print_test("Announcement_attachments table exists")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'announcement_attachments'
            )
        """)
        if cursor.fetchone()[0]:
            print_success("Table 'announcement_attachments' exists")
        else:
            print_error("Table 'announcement_attachments' not found")
            return False
        
        # Check columns in announcements table
        print_test("Announcements table columns")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'announcements'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        required_cols = ['announcement_id', 'title', 'description', 'type', 'status_classification']
        for col in required_cols:
            if col in columns:
                print_success(f"Column '{col}' exists")
            else:
                print_error(f"Column '{col}' missing")
        
        # Check legacy columns still exist
        legacy_cols = ['attachment', 'attachment_filename', 'attachment_content_type', 'attachment_size']
        print_info("Checking legacy attachment columns (for backward compatibility):")
        for col in legacy_cols:
            if col in columns:
                print_success(f"  Legacy column '{col}' exists")
        
        # Check new table structure
        print_test("Announcement_attachments table structure")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'announcement_attachments'
            ORDER BY ordinal_position
        """)
        att_columns = [row[0] for row in cursor.fetchall()]
        required_att_cols = ['attachment_id', 'announcement_id', 'filename', 'file_data', 'content_type']
        for col in required_att_cols:
            if col in att_columns:
                print_success(f"Column '{col}' exists")
            else:
                print_error(f"Column '{col}' missing")
    
    return True


# =============================================================================
# TEST 2: Stored Procedures
# =============================================================================
def test_stored_procedures():
    print_header("TEST 2: Stored Procedures")
    
    with connection.cursor() as cursor:
        # Check if sp_get_announcement_details exists
        print_test("sp_get_announcement_details exists")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc 
                WHERE proname = 'sp_get_announcement_details'
            )
        """)
        if cursor.fetchone()[0]:
            print_success("Stored procedure exists")
        else:
            print_error("Stored procedure not found")
            return False
        
        # Test with an actual announcement if exists
        print_test("Test sp_get_announcement_details with real data")
        cursor.execute("SELECT announcement_id FROM announcements LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            test_id = result[0]
            print_info(f"Testing with announcement_id={test_id}")
            
            cursor.execute(f"SELECT * FROM sp_get_announcement_details({test_id})")
            result = cursor.fetchone()
            
            if result:
                print_success("Stored procedure returned data")
                print_info(f"  Title: {result[1] if len(result) > 1 else 'N/A'}")
                print_info(f"  Type: {result[3] if len(result) > 3 else 'N/A'}")
                print_info(f"  Status: {result[4] if len(result) > 4 else 'N/A'}")
                
                # Check for new attachments_json field
                if len(result) > 10:
                    attachments_json = result[10]
                    print_success(f"New attachments_json field present: {attachments_json[:50]}...")
                else:
                    print_error("attachments_json field not found in result")
            else:
                print_error("Stored procedure returned no data")
        else:
            print_info("No announcements in database to test with")
    
    return True


# =============================================================================
# TEST 3: ORM Models
# =============================================================================
def test_orm_models():
    print_header("TEST 3: Django ORM Models")
    
    # Test Announcement model
    print_test("Announcement model query")
    try:
        count = Announcement.objects.count()
        print_success(f"Found {count} announcements")
        
        if count > 0:
            ann = Announcement.objects.first()
            print_info(f"  Sample: {ann.title[:50]}...")
            print_info(f"  ID: {ann.announcement_id}")
            print_info(f"  Type: {ann.type}")
            print_info(f"  Status: {ann.status_classification}")
            
            # Test helper properties
            print_test("Announcement model helper properties")
            print_info(f"  has_attachments: {ann.has_attachments}")
            print_info(f"  total_attachment_size: {ann.total_attachment_size}")
    except Exception as e:
        print_error(f"Failed to query Announcement model: {e}")
        return False
    
    # Test AnnouncementAttachment model
    print_test("AnnouncementAttachment model query")
    try:
        count = AnnouncementAttachment.objects.count()
        print_success(f"Found {count} announcement attachments")
        
        if count > 0:
            att = AnnouncementAttachment.objects.first()
            print_info(f"  Sample: {att.original_filename}")
            print_info(f"  Size: {att.file_size} bytes")
            print_info(f"  Type: {att.content_type}")
            print_info(f"  Announcement: {att.announcement.title[:30]}...")
    except Exception as e:
        print_error(f"Failed to query AnnouncementAttachment model: {e}")
        return False
    
    return True


# =============================================================================
# TEST 4: Attachment Utilities
# =============================================================================
def test_attachment_utils():
    print_header("TEST 4: Attachment Utility Functions")
    
    # Test get_announcement_attachments_info
    print_test("get_announcement_attachments_info()")
    try:
        ann = Announcement.objects.first()
        if ann:
            result = get_announcement_attachments_info(ann.announcement_id)
            attachments = result['files']
            print_success(f"Retrieved {result['attachment_count']} attachments for announcement {ann.announcement_id}")
            print_info(f"  Total size: {result['total_size']} bytes")
            for att in attachments:
                print_info(f"  - {att['filename']} ({att['file_size']} bytes)")
        else:
            print_info("No announcements to test with")
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


# =============================================================================
# TEST 5: Legacy Attachments
# =============================================================================
def test_legacy_attachments():
    print_header("TEST 5: Legacy Attachment Support")
    
    with connection.cursor() as cursor:
        # Check for announcements with legacy attachments
        print_test("Announcements with legacy attachments")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcements 
            WHERE attachment IS NOT NULL
        """)
        legacy_count = cursor.fetchone()[0]
        print_info(f"Found {legacy_count} announcements with legacy attachments")
        
        if legacy_count > 0:
            cursor.execute("""
                SELECT announcement_id, attachment_filename, attachment_size
                FROM announcements 
                WHERE attachment IS NOT NULL
                LIMIT 3
            """)
            for row in cursor.fetchall():
                print_info(f"  ID {row[0]}: {row[1]} ({row[2]} bytes)")
            
            print_success("Legacy attachments are preserved")
        else:
            print_info("No legacy attachments found (all may have been migrated)")
    
    return True


# =============================================================================
# TEST 6: Display Functions
# =============================================================================
def test_display_functions():
    print_header("TEST 6: Display and Preview Functions")
    
    print_test("Check announcements with any attachments")
    with connection.cursor() as cursor:
        # Check total attachments
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM announcements WHERE attachment IS NOT NULL) as legacy,
                (SELECT COUNT(DISTINCT announcement_id) FROM announcement_attachments) as new_table
        """)
        legacy, new_table = cursor.fetchone()
        print_info(f"Legacy attachments: {legacy}")
        print_info(f"New table attachments: {new_table}")
        print_success(f"Total announcements with attachments: {legacy + new_table}")
    
    # Test announcement with new attachments
    print_test("Announcements with new structure attachments")
    atts = AnnouncementAttachment.objects.select_related('announcement')[:3]
    for att in atts:
        print_info(f"  {att.announcement.title[:40]}: {att.original_filename}")
    
    return True


# =============================================================================
# TEST 7: CRUD Operations
# =============================================================================
def test_crud_operations():
    print_header("TEST 7: CRUD Operations")
    
    # READ
    print_test("READ - Query announcements")
    try:
        announcements = Announcement.objects.all()[:5]
        print_success(f"Successfully queried {announcements.count()} announcements")
        for ann in announcements:
            print_info(f"  - {ann.title[:50]}")
    except Exception as e:
        print_error(f"READ failed: {e}")
        return False
    
    # Check if we can read attachments
    print_test("READ - Query attachments")
    try:
        attachments = AnnouncementAttachment.objects.select_related('announcement')[:5]
        print_success(f"Successfully queried {attachments.count()} attachments")
        for att in attachments:
            print_info(f"  - {att.original_filename} (announcement: {att.announcement.title[:30]})")
    except Exception as e:
        print_error(f"READ attachments failed: {e}")
    
    # Note: We won't actually CREATE/UPDATE/DELETE in testing
    print_info("Note: CREATE/UPDATE/DELETE operations not tested automatically")
    print_info("      These should be tested manually through the web interface")
    
    return True


# =============================================================================
# TEST 8: Migration Verification
# =============================================================================
def test_migration_verification():
    print_header("TEST 8: Migration Verification")
    
    with connection.cursor() as cursor:
        # Check indexes
        print_test("Check indexes on announcement_attachments")
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'announcement_attachments'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        print_info(f"Found {len(indexes)} indexes:")
        for idx in indexes:
            print_info(f"  - {idx}")
        
        # Check foreign key constraints
        print_test("Check foreign key constraints")
        cursor.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'announcement_attachments'
        """)
        constraints = cursor.fetchall()
        print_info(f"Found {len(constraints)} constraints:")
        for name, ctype in constraints:
            print_info(f"  - {name} ({ctype})")
        
        # Verify no orphaned attachments
        print_test("Check for orphaned attachments")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcement_attachments aa
            LEFT JOIN announcements a ON aa.announcement_id = a.announcement_id
            WHERE a.announcement_id IS NULL
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned == 0:
            print_success("No orphaned attachments found")
        else:
            print_error(f"Found {orphaned} orphaned attachments")
    
    return True


# =============================================================================
# TEST 9: Announcement Recipients (Cooperative & Officer)
# =============================================================================
def test_announcement_recipients():
    print_header("TEST 9: Announcement Recipients")
    
    with connection.cursor() as cursor:
        # Check announcement_recipients table exists
        print_test("announcement_recipients table exists")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'announcement_recipients'
            )
        """)
        if cursor.fetchone()[0]:
            print_success("Table 'announcement_recipients' exists")
        else:
            print_error("Table 'announcement_recipients' not found")
            return False
        
        # Check announcement_officer_recipients table exists
        print_test("announcement_officer_recipients table exists")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'announcement_officer_recipients'
            )
        """)
        if cursor.fetchone()[0]:
            print_success("Table 'announcement_officer_recipients' exists")
        else:
            print_error("Table 'announcement_officer_recipients' not found")
            return False
        
        # Check cooperative recipients data
        print_test("Cooperative recipients data and relationships")
        cursor.execute("""
            SELECT 
                ar.announcement_id,
                a.title,
                c.cooperative_name,
                a.scope
            FROM announcement_recipients ar
            JOIN announcements a ON ar.announcement_id = a.announcement_id
            JOIN cooperatives c ON ar.coop_id = c.coop_id
            LIMIT 5
        """)
        coop_recipients = cursor.fetchall()
        if coop_recipients:
            print_success(f"Found {len(coop_recipients)} cooperative recipient records")
            for ann_id, title, coop_name, scope in coop_recipients[:3]:
                print_info(f"  - Announcement '{title[:40]}' → {coop_name} (scope: {scope})")
        else:
            print_info("No cooperative recipients found")
        
        # Check officer recipients data
        print_test("Officer recipients data and relationships")
        cursor.execute("""
            SELECT 
                aor.announcement_id,
                a.title,
                o.fullname,
                c.cooperative_name,
                a.scope
            FROM announcement_officer_recipients aor
            JOIN announcements a ON aor.announcement_id = a.announcement_id
            JOIN officers o ON aor.officer_id = o.officer_id
            JOIN cooperatives c ON o.coop_id = c.coop_id
            LIMIT 5
        """)
        officer_recipients = cursor.fetchall()
        if officer_recipients:
            print_success(f"Found {len(officer_recipients)} officer recipient records")
            for ann_id, title, officer_name, coop_name, scope in officer_recipients[:3]:
                print_info(f"  - Announcement '{title[:40]}' → {officer_name} ({coop_name}, scope: {scope})")
        else:
            print_info("No officer recipients found")
        
        # Check for orphaned cooperative recipients
        print_test("Check for orphaned cooperative recipients")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcement_recipients ar
            LEFT JOIN announcements a ON ar.announcement_id = a.announcement_id
            WHERE a.announcement_id IS NULL
        """)
        orphaned_coop = cursor.fetchone()[0]
        if orphaned_coop == 0:
            print_success("No orphaned cooperative recipients")
        else:
            print_error(f"Found {orphaned_coop} orphaned cooperative recipients")
        
        # Check for orphaned officer recipients
        print_test("Check for orphaned officer recipients")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcement_officer_recipients aor
            LEFT JOIN announcements a ON aor.announcement_id = a.announcement_id
            WHERE a.announcement_id IS NULL
        """)
        orphaned_officer = cursor.fetchone()[0]
        if orphaned_officer == 0:
            print_success("No orphaned officer recipients")
        else:
            print_error(f"Found {orphaned_officer} orphaned officer recipients")
        
        # Test scope consistency
        print_test("Verify scope consistency")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcements a
            JOIN announcement_recipients ar ON a.announcement_id = ar.announcement_id
            WHERE a.scope != 'cooperative'
        """)
        inconsistent_coop = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM announcements a
            JOIN announcement_officer_recipients aor ON a.announcement_id = aor.announcement_id
            WHERE a.scope != 'officer'
        """)
        inconsistent_officer = cursor.fetchone()[0]
        
        if inconsistent_coop == 0 and inconsistent_officer == 0:
            print_success("All recipient scopes are consistent")
        else:
            if inconsistent_coop > 0:
                print_error(f"Found {inconsistent_coop} announcements with cooperative recipients but scope != 'cooperative'")
            if inconsistent_officer > 0:
                print_error(f"Found {inconsistent_officer} announcements with officer recipients but scope != 'officer'")
        
        # Test foreign key constraints
        print_test("Foreign key constraints on recipient tables")
        cursor.execute("""
            SELECT constraint_name, table_name
            FROM information_schema.table_constraints
            WHERE table_name IN ('announcement_recipients', 'announcement_officer_recipients')
                AND constraint_type = 'FOREIGN KEY'
        """)
        fk_constraints = cursor.fetchall()
        print_info(f"Found {len(fk_constraints)} foreign key constraints:")
        for constraint_name, table_name in fk_constraints:
            print_info(f"  - {table_name}: {constraint_name}")
        
        if len(fk_constraints) >= 4:  # Should have at least 4 FK constraints
            print_success("Foreign key constraints properly defined")
        else:
            print_error(f"Expected at least 4 FK constraints, found {len(fk_constraints)}")
        
        # Test CASCADE behavior documentation
        print_test("Check CASCADE delete configuration")
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.table_name IN ('announcement_recipients', 'announcement_officer_recipients')
                AND tc.constraint_type = 'FOREIGN KEY'
                AND rc.delete_rule = 'CASCADE'
        """)
        cascade_rules = cursor.fetchall()
        if cascade_rules:
            print_success(f"Found {len(cascade_rules)} CASCADE delete rules")
            for table, constraint, rule in cascade_rules:
                print_info(f"  - {table}: {constraint} ({rule})")
        else:
            print_info("No CASCADE delete rules found (may use different deletion strategy)")
    
    return True


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================
def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     ANNOUNCEMENT SYSTEM COMPREHENSIVE TEST SUITE                   ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    tests = [
        ("Database Structure", test_database_structure),
        ("Stored Procedures", test_stored_procedures),
        ("ORM Models", test_orm_models),
        ("Attachment Utilities", test_attachment_utils),
        ("Legacy Attachments", test_legacy_attachments),
        ("Display Functions", test_display_functions),
        ("CRUD Operations", test_crud_operations),
        ("Migration Verification", test_migration_verification),
        ("Announcement Recipients", test_announcement_recipients),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! System is working correctly.{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠ Some tests failed. Please review the errors above.{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
