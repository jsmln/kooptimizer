from django.db import models
from apps.users.models import User  # Use custom User model, not Django's default
from apps.account_management.models import Cooperatives

class GenderEnum(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHERS = 'others', 'Others'

class ApprovalStatusEnum(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'

class ProfileData(models.Model):
    profile_id = models.AutoField(primary_key=True)
    # Changed to ForeignKey to allow multiple profile records per cooperative (one per year)
    coop = models.ForeignKey(Cooperatives, on_delete=models.CASCADE)
    
    # Report Year - similar to FinancialData
    report_year = models.IntegerField(null=True, blank=True)
    
    # Contact & Location
    address = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    email_address = models.CharField(max_length=100, null=True, blank=True)
    
    # Registration Info
    cda_registration_number = models.CharField(max_length=100, null=True, blank=True)
    cda_registration_date = models.DateField(null=True, blank=True)
    
    # LCCDC Membership
    lccdc_membership = models.BooleanField(null=True, blank=True)
    lccdc_membership_date = models.DateField(null=True, blank=True)
    
    # Operations
    operation_area = models.CharField(max_length=100, null=True, blank=True)
    business_activity = models.CharField(max_length=100, null=True, blank=True)
    
    # Metrics
    board_of_directors_count = models.IntegerField(null=True, blank=True)
    salaried_employees_count = models.IntegerField(null=True, blank=True)
    
    # Compliance & Certificates
    coc_renewal = models.BooleanField(null=True, blank=True)
    cote_renewal = models.BooleanField(null=True, blank=True)
    
    # BinaryFields store the raw file bytes (BYTEA in Postgres)
    coc_attachment = models.BinaryField(null=True, blank=True)
    cote_attachment = models.BinaryField(null=True, blank=True)
    
    approval_status = models.CharField(
        max_length=20, 
        choices=ApprovalStatusEnum.choices, 
        default=ApprovalStatusEnum.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profile_data'
        # Remove unique constraint - allow multiple profiles per coop (one per year)
        # Add unique constraint on coop_id + report_year combination
        unique_together = [['coop', 'report_year']]

class FinancialData(models.Model):
    financial_id = models.AutoField(primary_key=True)
    coop = models.ForeignKey(Cooperatives, on_delete=models.CASCADE)
    
    # Monetary fields
    assets = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    paid_up_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    net_surplus = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Stores combined file blobs
    attachments = models.BinaryField(null=True, blank=True)
    
    approval_status = models.CharField(
        max_length=20, 
        choices=ApprovalStatusEnum.choices, 
        default=ApprovalStatusEnum.PENDING
    )
    
    report_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_data'

class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    coop = models.ForeignKey(Cooperatives, on_delete=models.CASCADE)
    
    fullname = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GenderEnum.choices, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    # Note: email field removed - not used in members table
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members'

# ======================================================
# 3) STAFF MODEL
# ======================================================
class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True, db_column='staff_id')
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id', related_name='cooperatives_staff_profile')
    fullname = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True) # Mapped from 'gender_enum'
    mobile_number = models.CharField(max_length=20, blank=True, null=True, db_column='mobile_number')
    
    # --- NEW FIELD ---
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'staff'

    def __str__(self):
        # Return fullname if present, otherwise fallback to username (user may be required for Staff)
        return self.fullname or (getattr(self.user, 'username', '') or '');
    
# ======================================================
# 5) OFFICERS MODEL
# ======================================================
class Officer(models.Model):
    officer_id = models.AutoField(primary_key=True, db_column='officer_id')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_column='user_id', blank=True, null=True, related_name='cooperatives_officer_profile')
    coop = models.ForeignKey(Cooperatives, on_delete=models.CASCADE, db_column='coop_id')
    fullname = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True) # Mapped from 'gender_enum'
    mobile_number = models.CharField(max_length=20, blank=True, null=True, db_column='mobile_number')
    
    # --- NEW FIELD ---
    email = models.EmailField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        managed = False
        db_table = 'officers'

    def __str__(self):
        return self.fullname or str(self.user.username);