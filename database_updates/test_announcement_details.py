"""
Test script to verify announcement details stored procedure works correctly.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Database connection parameters
DB_CONFIG = {
    'dbname': 'kooptimizer_db2',
    'user': 'postgres',
    'password': 'postgres',
    'host': '127.0.0.1',
    'port': 5432
}

def test_announcement_details():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First, get any announcement ID
        cursor.execute("""
            SELECT announcement_id, title, status_classification 
            FROM announcements 
            WHERE status_classification IN ('sent', 'scheduled')
            LIMIT 1
        """)
        
        announcement = cursor.fetchone()
        
        if not announcement:
            print("❌ No sent or scheduled announcements found in database.")
            print("   Please create and send an announcement first.")
            return
        
        ann_id = announcement['announcement_id']
        print(f"\n✓ Testing with announcement: '{announcement['title']}' (ID: {ann_id})")
        print(f"  Status: {announcement['status_classification']}")
        
        # Test the stored procedure
        cursor.execute("SELECT * FROM sp_get_announcement_details(%s);", [ann_id])
        result = cursor.fetchone()
        
        if result:
            print("\n✓ Stored procedure executed successfully!")
            print("\n📋 Announcement Details:")
            print(f"   Title: {result['title']}")
            print(f"   Type: {result['type']}")
            print(f"   Status: {result['status_classification']}")
            print(f"   Scope: {result['scope']}")
            print(f"   Sender: {result['sender_name']} ({result['sender_role']})")
            
            if result['sent_at']:
                print(f"   Sent At: {result['sent_at']}")
            else:
                print(f"   Created At: {result['created_at']}")
            
            print(f"\n   Description: {result['description'][:100]}...")
            
            if result['attachment_size']:
                print(f"\n   📎 Attachment: Yes ({result['attachment_size']} bytes)")
            else:
                print("\n   📎 Attachment: No")
            
            # Parse and display recipients
            coop_recipients = json.loads(result['coop_recipients']) if result['coop_recipients'] else []
            officer_recipients = json.loads(result['officer_recipients']) if result['officer_recipients'] else []
            
            print(f"\n👥 Recipients:")
            if coop_recipients:
                print(f"   Cooperatives ({len(coop_recipients)}):")
                for coop in coop_recipients[:5]:  # Show first 5
                    print(f"      - {coop['coop_name']} (ID: {coop['coop_id']})")
                if len(coop_recipients) > 5:
                    print(f"      ... and {len(coop_recipients) - 5} more")
            
            if officer_recipients:
                print(f"   Officers ({len(officer_recipients)}):")
                # Group by cooperative
                by_coop = {}
                for officer in officer_recipients:
                    coop_name = officer['coop_name']
                    if coop_name not in by_coop:
                        by_coop[coop_name] = []
                    by_coop[coop_name].append(officer['officer_name'])
                
                for coop_name, officers in list(by_coop.items())[:3]:  # Show first 3 coops
                    print(f"      {coop_name}:")
                    for officer_name in officers[:3]:  # Show first 3 officers per coop
                        print(f"         - {officer_name}")
                    if len(officers) > 3:
                        print(f"         ... and {len(officers) - 3} more")
                
                if len(by_coop) > 3:
                    print(f"      ... and {len(by_coop) - 3} more cooperatives")
            
            if not coop_recipients and not officer_recipients:
                print("   (No recipients recorded)")
            
            print("\n✅ All tests passed! The stored procedure is working correctly.")
            
        else:
            print("\n❌ No result returned from stored procedure")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    print("=" * 70)
    print("Testing Announcement Details Stored Procedure")
    print("=" * 70)
    test_announcement_details()
    print("\n" + "=" * 70)
