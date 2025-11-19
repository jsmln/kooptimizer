import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import RequestFactory
from apps.communications.views import get_message_contacts
from django.contrib.sessions.middleware import SessionMiddleware

print("=" * 60)
print("TESTING get_message_contacts() VIEW")
print("=" * 60)

# Create a mock request
factory = RequestFactory()
request = factory.get('/communications/api/message/contacts/')

# Add session middleware
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session.save()

# Test with different user IDs and roles
test_users = [
    (1, 'admin'),   # Admin user
    (14, 'officer'), # Officer user
]

for user_id, role in test_users:
    print(f"\n{'='*60}")
    print(f"Testing as User ID {user_id} ({role.upper()})")
    print(f"{'='*60}")
    
    request.session['user_id'] = user_id
    request.session['role'] = role
    request.session.save()
    
    # Call the view
    response = get_message_contacts(request)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        
        if data['status'] == 'success':
            contacts = data['contacts']
            print(f"✓ Success: Found {len(contacts)} contacts")
            
            # Show first 3 contacts
            for i, contact in enumerate(contacts[:3], 1):
                print(f"  Contact {i}:")
                print(f"    Name: {contact['name']}")
                print(f"    User ID: {contact['user_id']}")
                print(f"    Role: {contact['role']}")
                print(f"    Coop: {contact.get('coop', 'N/A')}")
                print(f"    Last Message: {contact.get('last_message', 'N/A')[:50]}...")
                print(f"    Last Time: {contact.get('last_time', 'N/A')}")
        else:
            print(f"✗ Error: {data.get('message', 'Unknown error')}")
    else:
        print(f"✗ HTTP Error: {response.status_code}")
        print(response.content.decode('utf-8'))
