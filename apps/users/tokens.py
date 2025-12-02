from django.contrib.auth.tokens import PasswordResetTokenGenerator

class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        """
        Hash the user's primary key and some state that changes 
        if the password changes. This invalidates the token 
        once the password is reset.
        """
        # We use 'password_hash' instead of the standard 'password' field
        # We REMOVED 'last_login' from this check to fix your error.
        return (
            str(user.pk) + 
            str(timestamp) + 
            str(user.password_hash)
        )

# Create an instance to import in views
custom_token_generator = CustomTokenGenerator()