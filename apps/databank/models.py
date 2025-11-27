# apps/databank/models.py
from django.db import models
from django.conf import settings

class OCRScanSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='temp_ocr_scans/', null=True, blank=True) # <--- Added
    extracted_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_consumed = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']