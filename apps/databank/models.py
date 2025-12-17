# apps/databank/models.py
from django.db import models
from django.conf import settings

class OCRScanSession(models.Model):
    user_id = models.IntegerField(db_index=True)  # Store user_id directly instead of ForeignKey
    image = models.ImageField(upload_to='temp_ocr_scans/', null=True, blank=True)
    extracted_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_consumed = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        db_table = 'databank_ocrscansession'