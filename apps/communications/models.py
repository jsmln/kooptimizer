from django.db import DatabaseError, models, connection
from apps.users.models import User
# ======================================================
# 2) ADMIN MODEL
# ======================================================
class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True, db_column='admin_id')
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id', related_name='admin_profile')
    fullname = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True) # Mapped from 'gender_enum'
    mobile_number = models.CharField(max_length=20, blank=True, null=True, db_column='mobile_number')
    
    # --- NEW FIELD ---
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'admin'

    def __str__(self):
        return self.fullname or str(self.user.username)

# ======================================================
# 3) STAFF MODEL
# ======================================================
class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True, db_column='staff_id')
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id', related_name='staff_profile')
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
        return self.fullname or str(self.user.username)

# ======================================================
# 4) COOPERATIVES MODEL
# ======================================================
class Cooperative(models.Model):
    coop_id = models.AutoField(primary_key=True, db_column='coop_id')
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, db_column='staff_id', blank=True, null=True)
    admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, db_column='admin_id', blank=True, null=True)
    cooperative_name = models.CharField(max_length=200, unique=True, db_column='cooperative_name')
    mobile_number = models.CharField(max_length=20, blank=True, null=True, db_column='mobile_number')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        managed = False
        db_table = 'cooperatives'
    
    def __str__(self):
        return self.cooperative_name

# ======================================================
# 5) OFFICERS MODEL
# ======================================================
class Officer(models.Model):
    officer_id = models.AutoField(primary_key=True, db_column='officer_id')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_column='user_id', blank=True, null=True, related_name='officer_profile')
    coop = models.ForeignKey(Cooperative, on_delete=models.CASCADE, db_column='coop_id')
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
        return self.fullname or str(self.user.username)

# ======================================================
# 9) ANNOUNCEMENTS MODEL (Updated)
# ======================================================
class Announcement(models.Model):
    announcement_id = models.AutoField(primary_key=True, db_column='announcement_id')
    title = models.CharField(max_length=200)

    status_classification = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Sent'),
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled')
        ],
        default='draft',
        db_column='status_classification'
    )

    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, db_column='staff_id', blank=True, null=True)
    admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, db_column='admin_id', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, blank=True, null=True) # Mapped from 'announcement_type_enum'
    attachment = models.BinaryField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_column='sent_at')
    scope = models.CharField(max_length=50, blank=True, null=True)
    
    # This M2M field is for 'COOPERATIVE' scope
    coop_recipients = models.ManyToManyField(
        Cooperative, 
        through='AnnouncementRecipient',
        related_name='announcements'
    )

    # This M2M field is for 'OFFICER' scope
    officer_recipients = models.ManyToManyField(
        Officer,
        through='AnnouncementOfficerRecipient',
        related_name='announcements'
    )

    class Meta:
        managed = False
        db_table = 'announcements'

    def __str__(self):
        return self.title
    
    # --- NEW METHOD 1 ---
    @classmethod
    def get_by_status(cls, status):
        """
        Calls the sp_get_announcements_by_status stored procedure.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM sp_get_announcements_by_status(%s)", [status])
                # Convert the list of tuples into a list of dictionaries
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except DatabaseError as e:
            print(f"Database error in get_by_status: {e}")
            return [] # Return an empty list on error

    # --- NEW METHOD 2 ---
    @classmethod
    def save_announcement(cls, title, content, ann_type, status, scope,
                          creator_id, creator_role, coop_ids, officer_ids,
                          announcement_id=None, scheduled_time=None): # Added scheduled_time
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM sp_save_announcement(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [
                        title, content, ann_type, status, scope,
                        creator_id, creator_role, 
                        list(set(coop_ids)), list(set(officer_ids)), 
                        announcement_id, scheduled_time # Pass the time
                    ]
                )
                result = cursor.fetchone()
                if result: return result[0]
                return None
        except DatabaseError as e:
            print(f"Database error in save_announcement: {e}")
            return None # Return None on error

    class Meta:
        managed = False
        db_table = 'announcements'

    def __str__(self):
        return self.title

# ======================================================
# 10.1) ANNOUNCEMENT RECIPIENTS
# ======================================================
class AnnouncementRecipient(models.Model):
    announcement = models.OneToOneField(Announcement, on_delete=models.CASCADE, primary_key=True, db_column='announcement_id')
    coop = models.ForeignKey(Cooperative, on_delete=models.CASCADE, db_column='coop_id')

    class Meta:
        managed = False
        db_table = 'announcement_recipients'
        unique_together = (('announcement', 'coop'),)
        
# ======================================================
# 10.5) ANNOUNCEMENT OFFICER RECIPIENTS
# ======================================================
class AnnouncementOfficerRecipient(models.Model):
    announcement = models.OneToOneField(
        Announcement, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        db_column='announcement_id'
    )
    officer = models.ForeignKey(
        Officer, 
        on_delete=models.CASCADE, 
        db_column='officer_id'
    )

    class Meta:
        managed = False
        db_table = 'announcement_officer_recipients'
        unique_together = (('announcement', 'officer'),)