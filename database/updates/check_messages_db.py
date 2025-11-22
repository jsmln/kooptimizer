import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check messages table columns
print("=" * 60)
print("MESSAGES TABLE COLUMNS:")
print("=" * 60)
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='messages' 
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<30} {row[1]}")

# Check if messages exist
print("\n" + "=" * 60)
print("MESSAGES COUNT:")
print("=" * 60)
cursor.execute("SELECT COUNT(*) FROM messages")
count = cursor.fetchone()[0]
print(f"  Total messages: {count}")

# Check message_recipients
print("\n" + "=" * 60)
print("MESSAGE_RECIPIENTS COUNT:")
print("=" * 60)
cursor.execute("SELECT COUNT(*) FROM message_recipients")
count = cursor.fetchone()[0]
print(f"  Total message recipients: {count}")

# Check if sp_get_conversation exists
print("\n" + "=" * 60)
print("STORED PROCEDURE CHECK:")
print("=" * 60)
cursor.execute("""
    SELECT routine_name 
    FROM information_schema.routines 
    WHERE routine_name = 'sp_get_conversation'
""")
result = cursor.fetchone()
if result:
    print(f"  ✓ sp_get_conversation exists")
else:
    print(f"  ✗ sp_get_conversation NOT FOUND")

# Test the stored procedure with dummy data
print("\n" + "=" * 60)
print("TEST sp_get_conversation(1, 6):")
print("=" * 60)
try:
    cursor.execute("SELECT * FROM sp_get_conversation(1, 6)")
    rows = cursor.fetchall()
    print(f"  Rows returned: {len(rows)}")
    if rows:
        for i, row in enumerate(rows[:3], 1):  # Show first 3 messages
            print(f"  Message {i}: {row[3][:50]}..." if len(row[3]) > 50 else f"  Message {i}: {row[3]}")
except Exception as e:
    print(f"  Error: {e}")

# Check users table
print("\n" + "=" * 60)
print("USERS TABLE:")
print("=" * 60)
cursor.execute("SELECT user_id, username, role FROM users LIMIT 5")
for row in cursor.fetchall():
    print(f"  User ID {row[0]}: {row[1]} ({row[2]})")
