import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.test import RequestFactory
from apps.communications.views import get_conversation
from django.contrib.sessions.middleware import SessionMiddleware

print("=" * 60)
print("TESTING get_conversation() VIEW")
print("=" * 60)

# Create a mock request
factory = RequestFactory()

# Test conversation between user 1 (admin) and user 6 (officer)
print(f"\nTesting conversation: User 1 (admin) <-> User 6 (officer)")
print("=" * 60)

request = factory.get('/communications/api/message/conversation/6/')

# Add session middleware
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session['user_id'] = 1
request.session['role'] = 'admin'
request.session.save()

# Call the view
response = get_conversation(request, receiver_id=6)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    import json
    data = json.loads(response.content.decode('utf-8'))
    
    if data['status'] == 'success':
        messages = data['messages']
        print(f"✓ Success: Found {len(messages)} messages")
        print(f"  Receiver: {data['receiver_name']} (ID: {data['receiver_id']})")
        
        # Show first 5 messages
        for i, msg in enumerate(messages[:5], 1):
            msg_type = msg['type']
            text = msg['text'] if msg['text'] else '[Attachment]'
            has_att = '📎' if msg.get('has_attachment') else ''
            print(f"  Message {i} [{msg_type}]: {text[:60]}... {has_att}")
    else:
        print(f"✗ Error: {data.get('message', 'Unknown error')}")
else:
    print(f"✗ HTTP Error: {response.status_code}")
    print(response.content.decode('utf-8')[:200])
