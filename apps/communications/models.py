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
    cooperative_name = models.CharField(max_length=200, unique=True, db_column='cooperative_name')
    category = models.CharField(max_length=255, blank=True, null=True, db_column='category')
    district = models.CharField(max_length=255, blank=True, null=True, db_column='district')
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
# 8) MESSAGES MODEL
# ======================================================
class Message(models.Model):
    message_id = models.AutoField(primary_key=True, db_column='message_id')
    sender = models.ForeignKey('users.User', on_delete=models.SET_NULL, db_column='sender_id', blank=True, null=True, related_name='sent_messages')
    message = models.TextField()
    attachment = models.BinaryField(blank=True, null=True, db_column='attachment')
    attachment_filename = models.CharField(max_length=255, blank=True, null=True, db_column='attachment_filename')
    attachment_content_type = models.CharField(max_length=255, blank=True, null=True, db_column='attachment_content_type')
    attachment_size = models.BigIntegerField(blank=True, null=True, db_column='attachment_size')
    sent_at = models.DateTimeField(auto_now_add=True, db_column='sent_at')
    
    class Meta:
        managed = False
        db_table = 'messages'
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"

# ======================================================
# 8.5) MESSAGE RECIPIENTS MODEL
# ======================================================
# ... (Previous imports)

# Update MessageRecipient to track status
class MessageRecipient(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, db_column='message_id')
    receiver = models.ForeignKey('users.User', on_delete=models.CASCADE, db_column='receiver_id', related_name='received_messages')
    received_at = models.DateTimeField(blank=True, null=True, db_column='received_at')
    
    # --- NEW FIELDS ---
    status = models.CharField(
        max_length=20, 
        default='sent', 
        choices=[('sent', 'Sent'), ('delivered', 'Delivered'), ('seen', 'Seen')],
        db_column='status'
    )
    seen_at = models.DateTimeField(blank=True, null=True, db_column='seen_at')
    
    class Meta:
        managed = False
        db_table = 'message_recipients'
        unique_together = (('message', 'receiver'),)
        # Disable Django's automatic primary key creation
        # The table uses a composite PK (message_id, receiver_id)
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
    
    # DEPRECATED: These fields will be removed after migration
    # Use AnnouncementAttachment model instead
    attachment = models.BinaryField(blank=True, null=True)
    attachment_filename = models.CharField(max_length=255, blank=True, null=True, db_column='attachment_filename')
    attachment_content_type = models.CharField(max_length=255, blank=True, null=True, db_column='attachment_content_type')
    attachment_size = models.BigIntegerField(blank=True, null=True, db_column='attachment_size')
    
    sent_at = models.DateTimeField(blank=True, null=True, db_column='sent_at')
    scope = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
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
    
    # Helper property to check if announcement has attachments
    @property
    def has_attachments(self):
        """Check if announcement has attachments using new structure"""
        return self.attachments.exists()
    
    @property
    def total_attachment_size(self):
        """Calculate total size of all attachments"""
        from django.db.models import Sum
        result = self.attachments.aggregate(total=Sum('file_size'))
        return result['total'] or 0
    
    # --- NEW METHOD 1 ---
    @classmethod
    def get_by_status(cls, status):
        """
        Calls the sp_get_announcements_by_statuses stored procedure.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM sp_get_announcements_by_statuses(%s)", [status])
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
    
    @classmethod
    def get_draft_by_id(cls, announcement_id):
        """
        Retrieves a single draft announcement with all its recipients.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        a.announcement_id,
                        a.title,
                        a.description,
                        a.type,
                        a.status_classification,
                        a.scope, 
                        a.sent_at,
                        a.attachment_filename,
                        a.attachment_content_type,
                        a.attachment_size,
                        CASE WHEN a.attachment IS NOT NULL THEN TRUE ELSE FALSE END as has_attachment,
                        -- Cooperative recipients
                        COALESCE(
                            json_agg(
                                DISTINCT jsonb_build_object(
                                    'coop_id', ar.coop_id
                                )
                            ) FILTER (WHERE ar.coop_id IS NOT NULL),
                            '[]'::json
                        ) as coop_recipients,
                        -- Officer recipients
                        COALESCE(
                            json_agg(
                                DISTINCT jsonb_build_object(
                                    'officer_id', aor.officer_id,
                                    'coop_id', o.coop_id
                                )
                            ) FILTER (WHERE aor.officer_id IS NOT NULL),
                            '[]'::json
                        ) as officer_recipients
                    FROM announcements a
                    LEFT JOIN announcement_recipients ar ON a.announcement_id = ar.announcement_id
                    LEFT JOIN announcement_officer_recipients aor ON a.announcement_id = aor.announcement_id
                    LEFT JOIN officers o ON aor.officer_id = o.officer_id
                    WHERE a.announcement_id = %s
                    GROUP BY a.announcement_id
                """, [announcement_id])
                
                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                return None
        except DatabaseError as e:
            print(f"Database error in get_draft_by_id: {e}")
            return None
    
    @classmethod
    def get_recipients_for_announcement(cls, announcement_id):
        """
        Get recipient names and cooperative names for an announcement.
        Returns a dict with lists of officer names and cooperative names.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COALESCE(
                            json_agg(DISTINCT c.cooperative_name) FILTER (WHERE c.cooperative_name IS NOT NULL),
                            '[]'::json
                        ) as coop_names,
                        COALESCE(
                            json_agg(DISTINCT o.fullname) FILTER (WHERE o.fullname IS NOT NULL),
                            '[]'::json
                        ) as officer_names
                    FROM announcements a
                    LEFT JOIN announcement_recipients ar ON a.announcement_id = ar.announcement_id
                    LEFT JOIN cooperatives c ON ar.coop_id = c.coop_id
                    LEFT JOIN announcement_officer_recipients aor ON a.announcement_id = aor.announcement_id
                    LEFT JOIN officers o ON aor.officer_id = o.officer_id
                    WHERE a.announcement_id = %s
                """, [announcement_id])
                
                row = cursor.fetchone()
                if row:
                    return {
                        'coop_names': row[0] if row[0] else [],
                        'officer_names': row[1] if row[1] else []
                    }
                return {'coop_names': [], 'officer_names': []}
        except DatabaseError as e:
            print(f"Database error in get_recipients_for_announcement: {e}")
            return {'coop_names': [], 'officer_names': []}

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

# ======================================================
# 10.6) ANNOUNCEMENT ATTACHMENTS (NEW)
# ======================================================
class AnnouncementAttachment(models.Model):
    attachment_id = models.AutoField(primary_key=True, db_column='attachment_id')
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        db_column='announcement_id',
        related_name='attachments'
    )
    filename = models.CharField(max_length=255, db_column='filename')
    original_filename = models.CharField(max_length=255, db_column='original_filename')
    content_type = models.CharField(max_length=100, db_column='content_type')
    file_size = models.BigIntegerField(db_column='file_size')
    file_data = models.BinaryField(db_column='file_data')
    uploaded_at = models.DateTimeField(auto_now_add=True, db_column='uploaded_at')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_column='uploaded_by',
        null=True,
        blank=True,
        related_name='uploaded_announcement_attachments'
    )
    display_order = models.IntegerField(default=0, db_column='display_order')
    
    class Meta:
        managed = False
        db_table = 'announcement_attachments'
        ordering = ['display_order', 'attachment_id']
        indexes = [
            models.Index(fields=['announcement'], name='idx_ann_att_announcement'),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.announcement.title})"