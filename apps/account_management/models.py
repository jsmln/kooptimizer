# account_management/models.py

from django.db import models
from django.contrib.auth.hashers import make_password

# --- Enums (as TextChoices) ---
# These must match the ENUM types you defined in PostgreSQL

class GenderEnum(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHERS = 'others', 'Others'
    # Add any other values your 'gender_enum' type has

class UserRoleEnum(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    STAFF = 'staff', 'Staff'
    OFFICER = 'officer', 'Officer'
    # Add any other values your 'user_role_enum' type has

class VerificationStatusEnum(models.TextChoices):
    PENDING = 'pending', 'Pending'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'
    # Add any other values your 'verification_status_enum' type has


# --- Main Tables ---

class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, null=False)
    password_hash = models.CharField(max_length=128, null=False)
    role = models.CharField(max_length=50, choices=UserRoleEnum.choices, null=False)
    verification_status = models.CharField(
        max_length=50,
        choices=VerificationStatusEnum.choices,
        default=VerificationStatusEnum.PENDING
    )
    is_first_login = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    
    # **FIX:** Added is_active field for deactivation logic
    is_active = models.BooleanField(default=True)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    class Meta:
        db_table = 'users'

class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, db_column='user_id', null=False)
    fullname = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=50, choices=GenderEnum.choices, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'staff'

class Cooperatives(models.Model):
    coop_id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, db_column='staff_id', blank=True, null=True)
    cooperative_name = models.CharField(max_length=200, unique=True, null=False)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cooperatives'

class Officers(models.Model):
    officer_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, db_column='user_id', blank=True, null=True)
    coop = models.ForeignKey(Cooperatives, on_delete=models.CASCADE, db_column='coop_id', null=False)
    fullname = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=50, choices=GenderEnum.choices, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'officers'

class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, db_column='user_id', null=False)
    fullname = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=50, choices=GenderEnum.choices, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'admin'
