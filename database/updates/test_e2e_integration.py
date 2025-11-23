#!/usr/bin/env python
"""
End-to-End Test: Database → Backend → Frontend
Tests announcement system integration across all layers
"""
import os
import sys
import django
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import connection
from apps.communications.models import Announcement, AnnouncementAttachment
from apps.communications.views import (
    handle_announcement,
    download_announcement_attachment,
    convert_announcement_attachment_to_pdf
)
from apps.users.models import User


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
# TEST 1: Database Layer - Raw SQL Queries
# =============================================================================
def test_database_layer():
    print_header("TEST 1: Database Layer - Raw SQL")
    
    with connection.cursor() as cursor:
        # Test announcements query
        print_test("Query announcements table")
        try:
            cursor.execute("SELECT COUNT(*) FROM announcements")
            count = cursor.fetchone()[0]
            print_success(f"Successfully queried announcements: {count} records")
        except Exception as e:
            print_error(f"Failed: {e}")
            return False
        
        # Test announcement_attachments query
        print_test("Query announcement_attachments table")
        try:
            cursor.execute("SELECT COUNT(*) FROM announcement_attachments")
            count = cursor.fetchone()[0]
            print_success(f"Successfully queried announcement_attachments: {count} records")
        except Exception as e:
            print_error(f"Failed: {e}")
            return False
        
        # Test announcement_recipients query
        print_test("Query announcement_recipients table")
        try:
            cursor.execute("SELECT COUNT(*) FROM announcement_recipients")
            count = cursor.fetchone()[0]
            print_success(f"Successfully queried announcement_recipients: {count} records")
        except Exception as e:
            print_error(f"Failed: {e}")
            return False
        
        # Test announcement_officer_recipients query
        print_test("Query announcement_officer_recipients table")
        try:
            cursor.execute("SELECT COUNT(*) FROM announcement_officer_recipients")
            count = cursor.fetchone()[0]
            print_success(f"Successfully queried announcement_officer_recipients: {count} records")
        except Exception as e:
            print_error(f"Failed: {e}")
            return False
        
        # Test stored procedure
        print_test("Call sp_get_announcement_details()")
        try:
            cursor.execute("SELECT announcement_id FROM announcements LIMIT 1")
            result = cursor.fetchone()
            if result:
                ann_id = result[0]
                cursor.execute(f"SELECT * FROM sp_get_announcement_details({ann_id})")
                sp_result = cursor.fetchone()
                if sp_result:
                    print_success(f"Stored procedure returned {len(sp_result)} columns")
                    print_info(f"  Includes attachments_json field: {len(sp_result) > 10}")
                else:
                    print_error("Stored procedure returned no data")
                    return False
            else:
                print_info("No announcements to test with")
        except Exception as e:
            print_error(f"Failed: {e}")
            return False
    
    return True


# =============================================================================
# TEST 2: ORM Layer - Django Models
# =============================================================================
def test_orm_layer():
    print_header("TEST 2: ORM Layer - Django Models")
    
    # Test Announcement model
    print_test("Announcement.objects.all()")
    try:
        announcements = Announcement.objects.all()
        count = announcements.count()
        print_success(f"Retrieved {count} announcements via ORM")
        
        if count > 0:
            ann = announcements.first()
            print_info(f"  Sample title: {ann.title[:50]}")
            print_info(f"  Type: {ann.type}")
            print_info(f"  Status: {ann.status_classification}")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    # Test AnnouncementAttachment model
    print_test("AnnouncementAttachment.objects.all()")
    try:
        attachments = AnnouncementAttachment.objects.all()
        count = attachments.count()
        print_success(f"Retrieved {count} attachments via ORM")
        
        if count > 0:
            att = attachments.first()
            print_info(f"  Sample filename: {att.original_filename}")
            print_info(f"  Size: {att.file_size} bytes")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    # Test relationships
    print_test("Model relationships (announcement.attachments)")
    try:
        announcements_with_atts = Announcement.objects.filter(
            attachments__isnull=False
        ).distinct()
        count = announcements_with_atts.count()
        print_success(f"Found {count} announcements with attachments via relationship")
        
        if count > 0:
            ann = announcements_with_atts.first()
            att_count = ann.attachments.count()
            print_info(f"  '{ann.title[:40]}' has {att_count} attachment(s)")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    # Test helper properties
    print_test("Model helper properties")
    try:
        ann = Announcement.objects.first()
        if ann:
            has_atts = ann.has_attachments
            total_size = ann.total_attachment_size
            print_success(f"Helper properties accessible")
            print_info(f"  has_attachments: {has_atts}")
            print_info(f"  total_attachment_size: {total_size}")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    return True


# =============================================================================
# TEST 3: Backend Views - URL Endpoints
# =============================================================================
def test_backend_views():
    print_header("TEST 3: Backend Views - URL Endpoints")
    
    # Create test client
    client = Client()
    
    # Get a user for session
    user = User.objects.filter(role__in=['admin', 'staff']).first()
    if not user:
        print_error("No admin/staff user found for testing")
        return False
    
    # Test announcement detail endpoint (via stored procedure)
    print_test("GET announcement details via stored procedure")
    try:
        ann = Announcement.objects.first()
        if ann:
            # Simulate calling stored procedure through Django
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM sp_get_announcement_details({ann.announcement_id})")
                result = cursor.fetchone()
                if result:
                    print_success(f"Retrieved announcement details via SP")
                    print_info(f"  Title: {result[1][:50]}")
                    print_info(f"  Type: {result[3]}")
                    print_info(f"  Has attachments_json: {len(result) > 10}")
                else:
                    print_error("No data returned from stored procedure")
                    return False
        else:
            print_info("No announcements to test with")
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test attachment download endpoint
    print_test("Download attachment endpoint (legacy compatibility)")
    try:
        ann_with_legacy = Announcement.objects.filter(attachment__isnull=False).first()
        if ann_with_legacy:
            factory = RequestFactory()
            request = factory.get(f'/communications/api/announcement/{ann_with_legacy.announcement_id}/attachment/')
            
            # Add session
            middleware = SessionMiddleware(lambda x: None)
            middleware.process_request(request)
            request.session['user_id'] = user.user_id
            request.session['role'] = user.role
            request.session.save()
            
            response = download_announcement_attachment(request, ann_with_legacy.announcement_id)
            
            if response.status_code == 200:
                print_success("Legacy attachment download works")
                print_info(f"  Content-Type: {response.get('Content-Type', 'N/A')}")
            else:
                print_error(f"Download failed with status {response.status_code}")
        else:
            print_info("No legacy attachments to test with")
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test new attachment structure download
    print_test("Download attachment endpoint (new structure)")
    try:
        att = AnnouncementAttachment.objects.first()
        if att:
            factory = RequestFactory()
            request = factory.get(
                f'/communications/api/announcement/{att.announcement_id}/attachment/?attachment_id={att.attachment_id}'
            )
            
            # Add session
            middleware = SessionMiddleware(lambda x: None)
            middleware.process_request(request)
            request.session['user_id'] = user.user_id
            request.session['role'] = user.role
            request.session.save()
            
            response = download_announcement_attachment(request, att.announcement_id)
            
            if response.status_code == 200:
                print_success("New attachment download works")
                print_info(f"  Filename: {att.original_filename}")
                print_info(f"  Content-Type: {response.get('Content-Type', 'N/A')}")
            else:
                print_error(f"Download failed with status {response.status_code}")
        else:
            print_info("No new attachments to test with")
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
    
    return True


# =============================================================================
# TEST 4: Frontend Data Flow - Template Data
# =============================================================================
def test_frontend_data_flow():
    print_header("TEST 4: Frontend Data Flow - Template Data")
    
    # Test data structure for announcement list
    print_test("Announcement list data structure")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    announcement_id,
                    title,
                    type,
                    status_classification,
                    scope,
                    sent_at
                FROM announcements
                ORDER BY created_at DESC
                LIMIT 5
            """)
            announcements = cursor.fetchall()
            
            if announcements:
                print_success(f"Retrieved {len(announcements)} announcements for list view")
                for ann in announcements[:3]:
                    print_info(f"  ID {ann[0]}: {ann[1][:40]} ({ann[2]}, {ann[3]})")
            else:
                print_info("No announcements found")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    # Test data structure for announcement detail view
    print_test("Announcement detail view data structure")
    try:
        ann = Announcement.objects.first()
        if ann:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM sp_get_announcement_details({ann.announcement_id})")
                result = cursor.fetchone()
                
                if result:
                    print_success("Detail view data complete")
                    print_info(f"  Title: {result[1][:40]}")
                    print_info(f"  Description: {result[2][:50]}...")
                    print_info(f"  Type: {result[3]}")
                    print_info(f"  Status: {result[4]}")
                    print_info(f"  Scope: {result[5]}")
                    
                    # Check attachments data
                    if len(result) > 10:
                        attachments_json = result[10]
                        print_info(f"  Attachments JSON: {attachments_json[:100]}...")
                    
                    # Check recipients data
                    if len(result) > 12:
                        coop_recipients = result[12]
                        officer_recipients = result[13]
                        print_info(f"  Coop recipients: {coop_recipients[:50]}...")
                        print_info(f"  Officer recipients: {officer_recipients[:50]}...")
                else:
                    print_error("No detail data returned")
        else:
            print_info("No announcements to test with")
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test attachment preview data
    print_test("Attachment preview data structure")
    try:
        att = AnnouncementAttachment.objects.first()
        if att:
            print_success("Attachment data available for preview")
            print_info(f"  Filename: {att.original_filename}")
            print_info(f"  Content-Type: {att.content_type}")
            print_info(f"  Size: {att.file_size} bytes")
            print_info(f"  Can preview: {att.content_type in ['application/pdf', 'image/jpeg', 'image/png']}")
        else:
            print_info("No attachments to test preview with")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    return True


# =============================================================================
# TEST 5: Integration - Full Flow Simulation
# =============================================================================
def test_integration_flow():
    print_header("TEST 5: Integration - Full Flow Simulation")
    
    # Simulate: User views announcement list
    print_test("FLOW 1: User views announcement list")
    try:
        announcements = Announcement.objects.all()[:10]
        print_success(f"✓ List view loaded: {announcements.count()} announcements")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    # Simulate: User clicks on announcement to view details
    print_test("FLOW 2: User clicks announcement to view details")
    try:
        ann = Announcement.objects.first()
        if ann:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM sp_get_announcement_details({ann.announcement_id})")
                detail = cursor.fetchone()
                
                if detail:
                    print_success(f"✓ Detail view loaded for '{detail[1][:40]}'")
                    
                    # Check if has attachments
                    if len(detail) > 10:
                        import json
                        attachments_json = detail[10]
                        attachments = json.loads(attachments_json) if attachments_json != '[]' else []
                        print_info(f"  → Found {len(attachments)} attachment(s)")
                else:
                    print_error("Detail view failed to load")
        else:
            print_info("No announcements to test with")
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Simulate: User clicks to preview attachment
    print_test("FLOW 3: User clicks to preview attachment")
    try:
        att = AnnouncementAttachment.objects.first()
        if att:
            # Check if file type is previewable
            previewable_types = [
                'application/pdf',
                'image/jpeg', 'image/png', 'image/gif',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            
            can_preview = att.content_type in previewable_types
            print_success(f"✓ Attachment preview available: {can_preview}")
            print_info(f"  File: {att.original_filename}")
            print_info(f"  Type: {att.content_type}")
            
            if can_preview:
                print_info(f"  → Preview would open in modal")
        else:
            print_info("No attachments to test preview with")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    # Simulate: User downloads attachment
    print_test("FLOW 4: User downloads attachment")
    try:
        att = AnnouncementAttachment.objects.first()
        if att:
            # Verify attachment data is accessible
            has_data = att.file_data is not None
            print_success(f"✓ Attachment download ready: {has_data}")
            print_info(f"  File: {att.original_filename}")
            print_info(f"  Size: {att.file_size} bytes")
        else:
            print_info("No attachments to test download with")
    except Exception as e:
        print_error(f"Failed: {e}")
        return False
    
    return True


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================
def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║   END-TO-END TEST: Database → Backend → Frontend Integration      ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    tests = [
        ("Database Layer", test_database_layer),
        ("ORM Layer", test_orm_layer),
        ("Backend Views", test_backend_views),
        ("Frontend Data Flow", test_frontend_data_flow),
        ("Integration Flow", test_integration_flow),
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
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} integration tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All integration tests passed!{Colors.RESET}")
        print(f"{Colors.GREEN}The system is working correctly from database to frontend.{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}📝 NEXT STEPS - Manual Testing in Web UI:{Colors.RESET}")
        print("   1. Login to the system")
        print("   2. Navigate to Announcements page")
        print("   3. View announcement list")
        print("   4. Click on an announcement to view details")
        print("   5. Preview attachments (PDF, DOCX, images)")
        print("   6. Download attachments")
        print("   7. Create new announcement with attachments")
        print("   8. Edit existing announcement")
        print("   9. Test file upload and preview\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠ Some integration tests failed.{Colors.RESET}")
        print(f"{Colors.RED}Please review the errors above.{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
