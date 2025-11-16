"""
Test script for messaging stored procedures.
Inserts a test message using sp_send_message, then queries it using sp_get_conversation.
"""
import os
import sys
from datetime import datetime

# Ensure project path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')

import django
django.setup()

from django.db import connection
from apps.users.models import User
from apps.communications.models import Message, MessageRecipient

def test_messaging_sp():
    """
    Test the messaging stored procedures:
    1. Verify at least 2 users exist
    2. Use sp_send_message to insert a test message
    3. Use sp_get_conversation to retrieve it
    4. Verify both sender and receiver see the message
    """
    print("\n" + "="*70)
    print("MESSAGING STORED PROCEDURE TEST")
    print("="*70)

    # Step 1: Get test users
    print("\n[Step 1] Fetching test users...")
    users = User.objects.all()[:2]
    
    if len(users) < 2:
        print(f"ERROR: Not enough users. Found {len(users)}, need at least 2.")
        return False

    sender = users[0]
    receiver = users[1]
    print(f"✓ Sender: ID={sender.user_id}, Username={sender.username}, Role={sender.role}")
    print(f"✓ Receiver: ID={receiver.user_id}, Username={receiver.username}, Role={receiver.role}")

    # Step 2: Call sp_send_message
    print(f"\n[Step 2] Calling sp_send_message({sender.user_id}, {receiver.user_id}, 'Test message from SP')...")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM sp_send_message(%s, %s, %s);",
                [sender.user_id, receiver.user_id, "Test message from SP"]
            )
            result_row = cursor.fetchone()

        if not result_row:
            print("ERROR: sp_send_message returned no rows.")
            return False

        # row = (message_id, sender_id, receiver_id, message, attachment, attachment_filename, attachment_content_type, attachment_size, sent_at)
        (msg_id, sp_sender_id, sp_receiver_id, sp_message_text,
         sp_attachment, sp_attachment_filename, sp_attachment_content_type, sp_attachment_size, sp_sent_at) = result_row
        print(f"✓ sp_send_message succeeded:")
        print(f"  - Message ID: {msg_id}")
        print(f"  - Sender ID: {sp_sender_id}")
        print(f"  - Receiver ID: {sp_receiver_id}")
        print(f"  - Message: '{sp_message_text}'")
        print(f"  - Attachment filename: {sp_attachment_filename}")
        print(f"  - Attachment size: {sp_attachment_size}")
        print(f"  - Sent at: {sp_sent_at}")

    except Exception as e:
        print(f"ERROR executing sp_send_message: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Call sp_get_conversation
    print(f"\n[Step 3] Calling sp_get_conversation({sender.user_id}, {receiver.user_id})...")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM sp_get_conversation(%s, %s);",
                [sender.user_id, receiver.user_id]
            )
            conversation_rows = cursor.fetchall()

        if not conversation_rows:
            print("ERROR: sp_get_conversation returned no messages.")
            return False

        print(f"✓ sp_get_conversation returned {len(conversation_rows)} message(s):")
        for i, row in enumerate(conversation_rows, 1):
            (c_msg_id, c_sender_id, c_receiver_id, c_message,
             c_attachment, c_attachment_filename, c_attachment_content_type, c_attachment_size, c_sent_at) = row
            print(f"  [{i}] Message ID: {c_msg_id}, Sender: {c_sender_id}, Receiver: {c_receiver_id}")
            print(f"      Text: '{c_message}'")
            print(f"      Attachment: {c_attachment_filename} ({c_attachment_size})")
            print(f"      Sent at: {c_sent_at}")

        # Verify the test message is in the results
        test_msg_found = any(row[3] == "Test message from SP" for row in conversation_rows)
        if not test_msg_found:
            print(f"ERROR: Test message not found in conversation results.")
            return False

        print(f"✓ Test message found in conversation results.")

    except Exception as e:
        print(f"ERROR executing sp_get_conversation: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Verify reverse direction (receiver to sender)
    print(f"\n[Step 4] Verifying reverse direction sp_get_conversation({receiver.user_id}, {sender.user_id})...")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM sp_get_conversation(%s, %s);",
                [receiver.user_id, sender.user_id]
            )
            reverse_rows = cursor.fetchall()

        if not reverse_rows:
            print("ERROR: sp_get_conversation (reverse) returned no messages.")
            return False

        reverse_msg_found = any(row[3] == "Test message from SP" for row in reverse_rows)
        if not reverse_msg_found:
            print(f"ERROR: Test message not found in reverse conversation.")
            return False

        print(f"✓ Reverse direction also returns the message (both sides see it).")

    except Exception as e:
        print(f"ERROR executing sp_get_conversation (reverse): {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Verify DB state (direct query)
    print(f"\n[Step 5] Verifying message in DB tables...")
    try:
        message = Message.objects.get(message_id=msg_id)
        print(f"✓ Message record found in DB:")
        print(f"  - Message ID: {message.message_id}")
        print(f"  - Sender ID: {message.sender_id}")
        print(f"  - Text: '{message.message}'")
        print(f"  - Sent at: {message.sent_at}")

        # Query message_recipients directly using raw SQL since it has composite PK
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT message_id, receiver_id, received_at FROM message_recipients WHERE message_id = %s AND receiver_id = %s",
                [msg_id, receiver.user_id]
            )
            recipient_row = cursor.fetchone()

        if recipient_row:
            r_msg_id, r_receiver_id, r_received_at = recipient_row
            print(f"✓ Message recipient record found in DB:")
            print(f"  - Message ID: {r_msg_id}")
            print(f"  - Receiver ID: {r_receiver_id}")
            print(f"  - Received at: {r_received_at}")
        else:
            print(f"ERROR: Message recipient not found in DB.")
            return False

    except Exception as e:
        print(f"ERROR verifying DB state: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nSummary:")
    print(f"  - sp_send_message works: inserted message {msg_id}")
    print(f"  - sp_get_conversation works: retrieved messages in both directions")
    print(f"  - Both sender and receiver can see the message")
    print(f"  - Database records are correctly created")
    return True

if __name__ == '__main__':
    success = test_messaging_sp()
    sys.exit(0 if success else 1)
