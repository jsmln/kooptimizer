from django.db import models, connection
from django.conf import settings

# ===================================================
#  User Model
# ===================================================
class User(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='user_id')
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255, db_column='password_hash')
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
    is_online = models.BooleanField(default=False, db_column='is_online')
    last_active = models.DateTimeField(blank=True, null=True, db_column='last_active')
    is_active = models.BooleanField(default=True, db_column='is_active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False 
        db_table = 'users'

    def __str__(self):
        return self.username

    # Django auth compatibility properties
    @property
    def is_authenticated(self):
        """Required for Django authentication compatibility (used by webpush)"""
        return True
    
    @property
    def is_anonymous(self):
        """Required for Django authentication compatibility"""
        return False

    # Method to call stored procedure sp_login_user
    @staticmethod
    def login_user(username, password):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_login_user(%s, %s)", [username, password])
            result = cursor.fetchone()

        if result:
            return {
                'status': result[0],
                'user_id': result[1],
                'role': result[2],
                'verification_status': result[3],
                'is_first_login': result[4]
                
            }
        else:
            return None
    
    @staticmethod
    def complete_first_login(user_id, new_password_hash, verification_status):
        """
        Calls the stored procedure to update user status after first login.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM sp_complete_first_login(%s, %s, %s)",
                [user_id, new_password_hash, verification_status]
            )
        return True

    @property
    def mobile_number(self):
        """
        Fetches the mobile number from the correct role table
        by calling the sp_get_mobile_by_userid function.
        """
        with connection.cursor() as cursor:
            # Call the new SP we just created
            cursor.execute("SELECT * FROM sp_get_mobile_by_userid(%s)", [self.user_id])
            result = cursor.fetchone()
            
            if result and result[0]:
                return result[0]  # Return the mobile number
                
        return None
    
class Event(models.Model):
    # We MUST keep this relationship, otherwise the calendar breaks
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Adding the description field you requested
    description = models.TextField(blank=True, null=True)
    
    # We remove google_event_id since you didn't include it in your SQL

    class Meta:
        # THIS IS THE KEY: It forces Django to save to your specific table
        db_table = 'app_events'

    def __str__(self):
        return self.title
    
    