#!/usr/bin/env python
"""Find and fix announcements with incorrect scope"""
import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

print("\nFinding announcements with inconsistent scope...\n")

with connection.cursor() as cursor:
    # Find announcements with cooperative recipients but wrong scope
    cursor.execute("""
        SELECT 
            a.announcement_id,
            a.title,
            a.scope,
            c.cooperative_name
        FROM announcements a
        JOIN announcement_recipients ar ON a.announcement_id = ar.announcement_id
        JOIN cooperatives c ON ar.coop_id = c.coop_id
        WHERE a.scope != 'cooperative'
    """)
    
    coop_issues = cursor.fetchall()
    
    if coop_issues:
        print(f"Found {len(coop_issues)} announcement(s) with cooperative recipients but scope != 'cooperative':")
        print("-" * 80)
        for ann_id, title, scope, coop_name in coop_issues:
            print(f"ID: {ann_id}")
            print(f"Title: {title}")
            print(f"Current Scope: {scope}")
            print(f"Recipient: {coop_name}")
            print("-" * 80)
        
        print("\nDo you want to fix these by updating scope to 'cooperative'? (yes/no): ", end='')
        response = input().strip().lower()
        
        if response == 'yes':
            for ann_id, title, scope, coop_name in coop_issues:
                cursor.execute("""
                    UPDATE announcements 
                    SET scope = 'cooperative'
                    WHERE announcement_id = %s
                """, [ann_id])
                print(f"✓ Updated announcement {ann_id} scope to 'cooperative'")
            print("\n✓ All scopes fixed!")
        else:
            print("\nNo changes made.")
    else:
        print("✓ No cooperative scope issues found!")
    
    # Find announcements with officer recipients but wrong scope
    cursor.execute("""
        SELECT 
            a.announcement_id,
            a.title,
            a.scope,
            o.fullname
        FROM announcements a
        JOIN announcement_officer_recipients aor ON a.announcement_id = aor.announcement_id
        JOIN officers o ON aor.officer_id = o.officer_id
        WHERE a.scope != 'officer'
    """)
    
    officer_issues = cursor.fetchall()
    
    if officer_issues:
        print(f"\nFound {len(officer_issues)} announcement(s) with officer recipients but scope != 'officer':")
        print("-" * 80)
        for ann_id, title, scope, officer_name in officer_issues:
            print(f"ID: {ann_id}")
            print(f"Title: {title}")
            print(f"Current Scope: {scope}")
            print(f"Recipient: {officer_name}")
            print("-" * 80)
        
        print("\nDo you want to fix these by updating scope to 'officer'? (yes/no): ", end='')
        response = input().strip().lower()
        
        if response == 'yes':
            for ann_id, title, scope, officer_name in officer_issues:
                cursor.execute("""
                    UPDATE announcements 
                    SET scope = 'officer'
                    WHERE announcement_id = %s
                """, [ann_id])
                print(f"✓ Updated announcement {ann_id} scope to 'officer'")
            print("\n✓ All scopes fixed!")
        else:
            print("\nNo changes made.")
    else:
        print("\n✓ No officer scope issues found!")

print("\nDone!")
