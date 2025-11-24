# from django.db import models
# from apps.communications.models import Cooperative, Staff
# from apps.users.models import User

# class ProfileData(models.Model):
#     APPROVAL_CHOICES = [('Pending', 'pending'), ('Approved', 'approved')]
    
#     profile_id = models.AutoField(primary_key=True)
#     # Link to existing Cooperative model
#     coop = models.OneToOneField(
#         Cooperative, 
#         on_delete=models.CASCADE, 
#         db_column='coop_id', 
#         related_name='profile'
#     )
#     address = models.CharField(max_length=255, null=True, blank=True)
#     mobile_number = models.CharField(max_length=20, null=True, blank=True)
#     email_address = models.CharField(max_length=100, null=True, blank=True)
#     cda_registration_number = models.CharField(max_length=100, null=True, blank=True)
#     cda_registration_date = models.DateField(null=True, blank=True)
#     lccdc_membership = models.BooleanField(default=False, null=True)
#     lccdc_membership_date = models.DateField(null=True, blank=True)
#     operation_area = models.CharField(max_length=100, null=True, blank=True)
#     business_activity = models.CharField(max_length=100, null=True, blank=True)
#     board_of_directors_count = models.IntegerField(null=True, blank=True)
#     salaried_employees_count = models.IntegerField(null=True, blank=True)
#     coc_renewal = models.BooleanField(default=False, null=True)
#     cote_renewal = models.BooleanField(default=False, null=True)
    
#     # Binary fields for bytea columns
#     coc_attachment = models.BinaryField(null=True, blank=True)
#     cote_attachment = models.BinaryField(null=True, blank=True)
    
#     approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         managed = False 
#         db_table = 'profile_data'

# class FinancialData(models.Model):
#     APPROVAL_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')]

#     financial_id = models.AutoField(primary_key=True)
#     coop = models.ForeignKey(
#         Cooperative, 
#         on_delete=models.CASCADE, 
#         db_column='coop_id', 
#         related_name='financial_data'
#     )
#     assets = models.DecimalField(max_digits=20, decimal_places=2, default=0, null=True)
#     paid_up_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0, null=True)
#     net_surplus = models.DecimalField(max_digits=20, decimal_places=2, default=0, null=True)
#     attachments = models.BinaryField(null=True, blank=True)
#     approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, null=True, blank=True)
#     report_year = models.IntegerField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         managed = False
#         db_table = 'financial_data'

# class Member(models.Model):
#     GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    
#     member_id = models.AutoField(primary_key=True)
#     coop = models.ForeignKey(
#         Cooperative, 
#         on_delete=models.CASCADE, 
#         db_column='coop_id', 
#         related_name='members'
#     )
#     fullname = models.CharField(max_length=100)
#     gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         managed = False
#         db_table = 'members'