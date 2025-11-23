"""
Script to create sp_reactivate_user stored procedure
"""
import psycopg2

# Database connection
conn = psycopg2.connect(
    dbname="kooptimizer_db2",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

# Direct SQL - easier than parsing file
sql = """
CREATE OR REPLACE PROCEDURE sp_reactivate_user(
    p_user_id INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Validate that user exists
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = p_user_id) THEN
        RAISE EXCEPTION 'User with ID % not found', p_user_id;
    END IF;

    -- Check if user is already active
    IF EXISTS (SELECT 1 FROM users WHERE user_id = p_user_id AND is_active = TRUE) THEN
        RAISE EXCEPTION 'User account is already active';
    END IF;

    -- Reactivate the user
    UPDATE users
    SET is_active = TRUE
    WHERE user_id = p_user_id;

    -- Log success
    RAISE NOTICE 'User account % has been reactivated successfully', p_user_id;
    
END;
$$;
"""

print("Creating sp_reactivate_user procedure...")
try:
    cursor.execute(sql)
    conn.commit()
    print("✓ Procedure created successfully!")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

# Test that it exists
cursor.execute("""
    SELECT routine_name, routine_type
    FROM information_schema.routines
    WHERE routine_name = 'sp_reactivate_user'
    AND routine_schema = 'public'
""")

result = cursor.fetchone()
if result:
    print(f"✓ Verified: {result[0]} ({result[1]}) exists in database")
else:
    print("✗ Procedure not found!")

cursor.close()
conn.close()
