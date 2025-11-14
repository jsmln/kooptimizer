from django.contrib.auth.hashers import PBKDF2PasswordHasher

# --- Your input values ---
password_to_hash = "StaffM123"
salt = "mMogCn84UFOf6yDf83ZjqO"
iterations = 1000000
original_hash = "pbkdf2_sha256$1000000$mMogCn84UFOf6yDf83ZjqO$O8u6S6iCXiLhDDA/i1P5aBceg7iX9XCMfalRmhiqBo0="
# --------------------------

# 1. Create an instance of the correct hasher
#    This is the default hasher for PBKDF2 with SHA256
hasher = PBKDF2PasswordHasher()

# 2. Set the exact number of iterations you want
hasher.iterations = iterations

# 3. Encode the password using your specific salt
#    The 'encode' method combines the algorithm, iterations, salt,
#    and the newly hashed password into the standard string format.
generated_hash = hasher.encode(password_to_hash, salt)

# --- Output and Verification ---
print(f"Password:   {password_to_hash}")
print(f"Salt:       {salt}")
print(f"Iterations: {iterations}\n")

print(f"Generated Hash: {generated_hash}")
print(f"Original Hash:  {original_hash}\n")

# Verify that the generated hash matches the original
if generated_hash == original_hash:
    print("✅ Success: The generated hash matches the original hash.")
else:
    print("❌ Failure: Hashes do not match.")