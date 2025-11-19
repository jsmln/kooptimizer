import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os
import django

# --- Initialize Django Environment ---
# !! IMPORTANT: Change 'your_project_name.settings' to your project's settings file !!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings') 
try:
    django.setup()
except ImportError:
    print("Error: Could not import Django.")
    print("Make sure 'your_project_name.settings' is correct and your project is in the Python path.")
    sys.exit(1)
# --- End Django Setup ---

from django.contrib.auth.hashers import make_password

# Fix Unicode output in Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

def register_user(username: str, password: str, role: str):
    """
    Calls the PostgreSQL stored procedure sp_register_user
    to register a new user securely with bcrypt hashing.
    """
    conn = None
    try:
        hashed_password = make_password(password)

        conn = psycopg2.connect(
            host="127.0.0.1",
            database="kooptimizer_db2",
            user="postgres",
            password="postgres"
        )
        conn.autocommit = True

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM public.sp_register_user(%s, %s, %s);
            """, (username, hashed_password, role))

            result = cur.fetchone()
            return result 

    except psycopg2.Error as e:
        print("Database error:", e)
        return None
    except Exception as e:
        print(f"A general error occurred: {e}")
        return None
    finally:
        if conn:
            conn.close()


# ======================================================
# Example Usage: register 'admin_user'
# ======================================================
if __name__ == "__main__":
    # REMINDER: You must change 'your_project_name.settings' at the top 
    # of this file for this script to run.
    new_user = register_user("admin_user", "pbkdf2_sha256$1000000$yJHpU2aSZEzp3cknr6gh5i$ID51SIGSmibymbCaXIPm79LFx2xAjB9UHEMi2iNsqOE=", "admin")

    if new_user:
        print("✅ User registered successfully:")
        print(new_user)
    else:
        print("⚠️ Username already exists or error occurred.")