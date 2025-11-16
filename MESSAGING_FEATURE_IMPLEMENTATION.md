# Messaging Feature Implementation Guide

## Overview
This document describes the complete messaging feature implementation for Kooptimizer, including role-based access control, database integration, and dynamic UI rendering.

---

## Database Schema

### Tables Used
The implementation leverages two existing database tables:

#### 1. `messages` Table
```sql
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### 2. `message_recipients` Table
```sql
CREATE TABLE message_recipients (
    message_id INTEGER NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    received_at TIMESTAMPTZ,
    PRIMARY KEY (message_id, receiver_id)
);
```

---

## Backend Implementation

### 1. Django Models (`apps/communications/models.py`)

Two new models were added:

```python
class Message(models.Model):
    message_id = models.AutoField(primary_key=True, db_column='message_id')
    sender = models.ForeignKey('users.User', on_delete=models.SET_NULL, 
                              db_column='sender_id', blank=True, null=True, 
                              related_name='sent_messages')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True, db_column='sent_at')
    
    class Meta:
        managed = False
        db_table = 'messages'

class MessageRecipient(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, db_column='message_id')
    receiver = models.ForeignKey('users.User', on_delete=models.CASCADE, 
                                db_column='receiver_id', related_name='received_messages')
    received_at = models.DateTimeField(blank=True, null=True, db_column='received_at')
    
    class Meta:
        managed = False
        db_table = 'message_recipients'
        unique_together = (('message', 'receiver'),)
```

### 2. Django Views (`apps/communications/views.py`)

Four new API endpoints and one view were implemented:

#### A. `get_message_contacts()` - GET Endpoint
**Purpose:** Fetch available contacts based on user role

**Role-Based Logic:**
- **ADMIN**: Can see all officers, grouped by cooperative
- **STAFF**: Can see admin + officers in their assigned cooperatives
- **OFFICER**: Can see admin + their assigned staff handler

```python
@require_http_methods(["GET"])
def get_message_contacts(request):
    # Returns JSON with structure:
    # {
    #   "status": "success",
    #   "contacts": [
    #     {
    #       "group": "Cooperative Name",  // For admin
    #       "items": [{ "user_id", "name", "role", "avatar", ... }]
    #     },
    #     { "user_id", "name", "role", "avatar", ... }  // Single contact
    #   ]
    # }
```

#### B. `get_conversation()` - GET Endpoint
**Purpose:** Load message history between two users

```python
@require_http_methods(["GET"])
def get_conversation(request, receiver_id):
    # Returns JSON with:
    # {
    #   "status": "success",
    #   "receiver_id": <id>,
    #   "receiver_name": "<name>",
    #   "receiver_avatar": "<initial>",
    #   "messages": [
    #     {
    #       "message_id": <id>,
    #       "text": "<message>",
    #       "type": "incoming" | "outgoing",
    #       "time": "<ISO timestamp>",
    #       "sender_id": <id>
    #     }, ...
    #   ]
    # }
```

#### C. `send_message()` - POST Endpoint
**Purpose:** Send a new message with role-based permission validation

**Permission Rules:**
- **ADMIN** → Can send to any **OFFICER**
- **STAFF** → Can send to **ADMIN** or **OFFICER** in their cooperatives
- **OFFICER** → Can send to **ADMIN** or their assigned **STAFF** handler

```python
@require_POST
@csrf_exempt
def send_message(request):
    # Expects JSON:
    # { "receiver_id": <id>, "message": "<text>" }
    
    # Returns:
    # { "status": "success", "message_id": <id>, "sent_at": "<timestamp>" }
```

#### D. `message_view()` - Render View
**Purpose:** Render the messages page template

---

## URL Routing (`apps/communications/urls.py`)

```python
urlpatterns = [
    path('message/', views.message_view, name='message'),
    path('api/message/contacts/', views.get_message_contacts, name='get_message_contacts'),
    path('api/message/conversation/<int:receiver_id>/', views.get_conversation, name='get_conversation'),
    path('api/message/send/', views.send_message, name='send_message'),
]
```

---

## Frontend Implementation

### 1. Template (`templates/communications/message.html`)

The template is fully dynamic and uses JavaScript to:
- Fetch contacts from the backend API
- Display different contact lists based on user role
- Load and display message history
- Send new messages

**Key Features:**
- **Dynamic Contact Loading:** Contacts are fetched via AJAX and rendered based on role
- **Grouped Display:** For admin users, contacts are grouped by cooperative
- **Real-time Updates:** Timestamps update every 10 seconds
- **Search Functionality:** Filter contacts by name
- **New Message Modal:** Dialog to start new conversations

### 2. JavaScript Functions

#### Contact Loading
```javascript
async function loadContacts()
// Fetches available contacts from /communications/api/message/contacts/
```

#### Conversation Loading
```javascript
async function loadConversation(receiverId)
// Fetches message history from /communications/api/message/conversation/<id>/
```

#### Message Sending
```javascript
async function sendMessage()
// Sends message via POST to /communications/api/message/send/
// Reloads conversation on success
```

---

## Role-Based Access Control Summary

| User Role | Can Message | Notes |
|-----------|------------|-------|
| **ADMIN** | Any Officer | Can send to all officers across all cooperatives |
| **STAFF** | Admin + Their Officers | Can only message officers in their assigned cooperatives |
| **OFFICER** | Admin + Their Handler | Can only message admin or their assigned staff handler |

---

## Features Implemented

✅ **Dynamic Contact Display**
- Admin sees officers grouped by cooperative
- Staff sees admin + their assigned officers
- Officers see admin + their staff handler

✅ **Role-Based Messaging Permissions**
- Backend enforces permission rules
- Frontend respects role constraints

✅ **Message History**
- Bi-directional conversation view
- Distinguishes incoming vs outgoing messages
- Displays message timestamps (relative and absolute)

✅ **Search & Filter**
- Filter contacts by name
- Real-time search results

✅ **New Message Modal**
- Start new conversations
- Modal displays appropriate contacts based on role

✅ **Real-time UI Updates**
- Timestamps auto-update every 10 seconds
- "Just now" → minutes → hours → days ago

---

## API Response Examples

### Get Contacts (ADMIN)
```json
{
  "status": "success",
  "contacts": [
    {
      "group": "Cooperative A",
      "items": [
        {
          "user_id": 10,
          "name": "Juan Dela Cruz",
          "role": "officer",
          "avatar": "J",
          "position": "President",
          "coop": "Cooperative A"
        }
      ]
    }
  ]
}
```

### Get Contacts (STAFF)
```json
{
  "status": "success",
  "contacts": [
    {
      "user_id": 1,
      "name": "Admin User",
      "role": "admin",
      "avatar": "A",
      "position": "Admin"
    },
    {
      "user_id": 10,
      "name": "Juan Dela Cruz",
      "role": "officer",
      "avatar": "J",
      "position": "President",
      "coop": "Cooperative A"
    }
  ]
}
```

### Get Conversation
```json
{
  "status": "success",
  "receiver_id": 10,
  "receiver_name": "Juan Dela Cruz",
  "receiver_avatar": "J",
  "messages": [
    {
      "message_id": 1,
      "text": "Hello, how are you?",
      "type": "outgoing",
      "time": "2025-11-15T10:30:00Z",
      "sender_id": 5
    },
    {
      "message_id": 2,
      "text": "I'm doing well, thanks!",
      "type": "incoming",
      "time": "2025-11-15T10:35:00Z",
      "sender_id": 10
    }
  ]
}
```

### Send Message
```json
{
  "status": "success",
  "message_id": 3,
  "sent_at": "2025-11-15T10:40:00Z"
}
```

---

## Error Handling

### Common Errors

1. **User Not Authenticated**
   - Status: 401
   - Message: "User not authenticated"

2. **Missing Required Data**
   - Status: 400
   - Message: "Missing receiver or message"

3. **Permission Denied**
   - Status: 403
   - Message: "You do not have permission to message this user"

4. **Receiver Not Found**
   - Status: 404
   - Message: "Receiver not found"

5. **Server Error**
   - Status: 500
   - Message: "<error details>"

---

## Session Requirements

The backend expects the following in `request.session`:
- `user_id`: Integer user ID
- `role`: String ('admin', 'staff', or 'officer')

These should be set during login.

---

## Testing Checklist

- [ ] Admin can see all officers grouped by cooperative
- [ ] Staff can see admin + officers in their cooperatives
- [ ] Officer can see admin + their staff handler
- [ ] Messages send successfully
- [ ] Permission validation works (no cross-role messaging)
- [ ] Message history displays correctly
- [ ] Timestamps update dynamically
- [ ] Search/filter works
- [ ] New message modal appears
- [ ] Error messages display appropriately

---

## Future Enhancements

Possible improvements for future iterations:

1. **File Attachments** - Allow users to send files/images
2. **Message Status** - Read receipts, delivery confirmation
3. **Notifications** - Real-time message notifications
4. **Message Reactions** - Emoji reactions to messages
5. **Group Messaging** - Messages to multiple recipients
6. **Message Archiving** - Archive old conversations
7. **Message Search** - Search within conversations
8. **Typing Indicators** - Show when user is typing

---

## Files Modified

1. `apps/communications/models.py` - Added Message & MessageRecipient models
2. `apps/communications/views.py` - Added 4 new views + 1 API endpoint
3. `apps/communications/urls.py` - Added 4 new URL patterns
4. `templates/communications/message.html` - Complete template rewrite with dynamic JS

---

## Notes

- All timestamps are stored in PostgreSQL with `TIMESTAMPTZ` for timezone awareness
- Messages are immutable once sent (no edit/delete implemented yet)
- Frontend handles escaping to prevent XSS attacks
- Permission validation happens on both backend and frontend
- API uses JSON for all requests/responses
