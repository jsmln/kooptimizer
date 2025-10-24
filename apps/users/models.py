from django.db import models


class User(models.Model):
    # Use user_id as the primary key to match existing DB schema
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)  # This will store the hashed password
    role = models.CharField(max_length=50)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified')
        ],
        default='pending'
    )
    is_first_login = models.BooleanField(default=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'  # Specify the table name explicitly

    def __str__(self):
        return self.username
