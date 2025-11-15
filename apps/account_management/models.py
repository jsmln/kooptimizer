from django.db import models

class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=20)  # matching enum
    is_first_login = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='staff_profile')
    fullname = models.CharField(max_length=100, null=True)
    position = models.CharField(max_length=50, null=True)
    mobile_number = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=100, unique=True, null=True)

    class Meta:
        db_table = 'staff'

class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='admin_profile')
    fullname = models.CharField(max_length=100, null=True)
    position = models.CharField(max_length=50, null=True)
    mobile_number = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=100, unique=True, null=True)

    class Meta:
        db_table = 'admin'

class Cooperatives(models.Model):
    coop_id = models.AutoField(primary_key=True)
    cooperative_name = models.CharField(max_length=200, unique=True)
    # Linking based on your SQL schema
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'cooperatives'

class Officers(models.Model):
    officer_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='officer_profile')
    coop = models.ForeignKey(Cooperatives, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=100, null=True)
    position = models.CharField(max_length=50, null=True)
    mobile_number = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = 'officers'