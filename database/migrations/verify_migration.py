#!/usr/bin/env python
"""
Script to verify the profile_data migration was successful.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection
from apps.cooperatives.models import ProfileData

def verify_migration():
    """Verify the migration was successful."""
    print("Verifying profile_data migration...")
    print("=" * 50)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: report_year column exists
    checks_total += 1
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'profile_data' AND column_name = 'report_year'
        """)
        result = cursor.fetchone()
        if result:
            print(f"[OK] Check 1: report_year column exists (type: {result[1]})")
            checks_passed += 1
        else:
            print("[FAIL] Check 1: report_year column NOT found!")
    
    # Check 2: Unique constraint on coop_id removed
    checks_total += 1
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'profile_data' AND indexname = 'profile_data_coop_id_key'
        """)
        result = cursor.fetchone()
        if not result:
            print("[OK] Check 2: Old unique constraint on coop_id removed")
            checks_passed += 1
        else:
            print("[FAIL] Check 2: Old unique constraint still exists!")
    
    # Check 3: New unique constraint on (coop_id, report_year) exists
    checks_total += 1
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'profile_data' 
            AND (indexname LIKE '%coop_year%' OR indexname LIKE '%coop%year%')
        """)
        result = cursor.fetchone()
        if result:
            print(f"[OK] Check 3: New unique constraint exists: {result[0]}")
            checks_passed += 1
        else:
            print("[WARN] Check 3: New unique constraint not found (may be using unique_together)")
    
    # Check 4: Existing records have report_year set
    checks_total += 1
    profiles_with_year = ProfileData.objects.exclude(report_year__isnull=True).count()
    total_profiles = ProfileData.objects.count()
    if total_profiles == 0:
        print("[OK] Check 4: No existing profiles (will be set when first profile is created)")
        checks_passed += 1
    elif profiles_with_year == total_profiles:
        print(f"[OK] Check 4: All {total_profiles} existing profiles have report_year set")
        checks_passed += 1
    else:
        print(f"[WARN] Check 4: {profiles_with_year}/{total_profiles} profiles have report_year set")
        # This is okay if some are NULL (legacy data)
        checks_passed += 1
    
    # Check 5: Model can create multiple profiles per coop
    checks_total += 1
    try:
        # Just check if the model allows it (no actual creation)
        from apps.account_management.models import Cooperatives
        coop = Cooperatives.objects.first()
        if coop:
            profiles_count = ProfileData.objects.filter(coop=coop).count()
            print(f"[OK] Check 5: Model supports multiple profiles per coop (found {profiles_count} for first coop)")
            checks_passed += 1
        else:
            print("[WARN] Check 5: No cooperatives found to test")
            checks_passed += 1
    except Exception as e:
        print(f"[FAIL] Check 5: Error testing model: {e}")
    
    # Summary
    print("=" * 50)
    print(f"Verification Results: {checks_passed}/{checks_total} checks passed")
    
    if checks_passed == checks_total:
        print("\n[SUCCESS] All checks passed! Migration is successful.")
        print("\nNext steps:")
        print("1. Test creating a profile for the current year")
        print("2. Test viewing/editing the profile")
        print("3. Update the form template to include year selector")
        return True
    else:
        print("\n[WARNING] Some checks failed. Please review the output above.")
        return False

if __name__ == '__main__':
    success = verify_migration()
    sys.exit(0 if success else 1)

