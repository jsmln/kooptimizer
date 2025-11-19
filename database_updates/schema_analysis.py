"""
Database Schema vs Django Models Comparison
============================================

ACTUAL DATABASE SCHEMA:
-----------------------

cooperatives:
  - coop_id (integer, NOT NULL)
  - staff_id (integer, NULL)
  - cooperative_name (varchar, NOT NULL)
  - created_at (timestamp, NOT NULL)
  - updated_at (timestamp, NOT NULL)
  - category (varchar, NULL)          <-- MISSING in models
  - district (varchar, NULL)          <-- MISSING in models

admin, staff, officers:
  - ALL have mobile_number (varchar, NULL)  ✓ Correct

profile_data:
  - mobile_number (varchar, NULL)  ✓ Correct (contact info for coop)

users:
  - is_online (boolean, NULL)
  - last_active (timestamp, NULL)
  - is_active (boolean, NULL)

message_recipients:
  - status (varchar, NULL)
  - seen_at (timestamp, NULL)
"""
print(__doc__)
