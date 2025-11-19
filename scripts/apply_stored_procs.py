import os
import sys

# Ensure project path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')

import django
django.setup()

from django.db import connection

SQL_FILES = [
    os.path.join(BASE_DIR, 'stored_procedures', 'alter_messages_add_attachment.sql'),
    os.path.join(BASE_DIR, 'stored_procedures', 'sp_send_message.sql'),
    os.path.join(BASE_DIR, 'stored_procedures', 'sp_get_conversation.sql'),
    os.path.join(BASE_DIR, 'stored_procedures', 'sp_get_announcement_details.sql'),
    os.path.join(BASE_DIR, 'stored_procedures', 'sp_save_announcement.sql'),
]

def apply_sql_file(path):
    print(f"Applying {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        # Use autocommit for DDL
        with connection.cursor() as cur:
            connection.autocommit = True
            # If updating sp_get_conversation or sp_send_message, drop existing functions first to avoid type-change errors
            base = os.path.basename(path).lower()
            if base == 'sp_get_conversation.sql':
                try:
                    cur.execute('DROP FUNCTION IF EXISTS sp_get_conversation(integer, integer) CASCADE;')
                except Exception:
                    pass
            if base == 'sp_send_message.sql':
                try:
                    cur.execute('DROP FUNCTION IF EXISTS sp_send_message(integer, integer, text, bytea, text, text, bigint) CASCADE;')
                    # Also drop older 3-arg overload if present to avoid ambiguity
                    try:
                        cur.execute('DROP FUNCTION IF EXISTS sp_send_message(integer, integer, text) CASCADE;')
                    except Exception:
                        pass
                except Exception:
                    pass
            cur.execute(sql)
        print(f"Applied {os.path.basename(path)} successfully.")
    except Exception as e:
        print(f"Failed to apply {os.path.basename(path)}: {e}")
        raise

def main():
    for path in SQL_FILES:
        if not os.path.exists(path):
            print(f"SQL file not found: {path}")
            continue
        apply_sql_file(path)

if __name__ == '__main__':
    main()
