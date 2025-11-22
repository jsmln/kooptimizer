import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.utils import timezone
from apps.communications.models import Announcement

# Check scheduled announcements
scheduled = Announcement.objects.filter(status_classification='scheduled')
print(f'Found {scheduled.count()} scheduled announcements')

for a in scheduled:
    print(f'\nID: {a.announcement_id}')
    print(f'Title: {a.title}')
    print(f'Scheduled time: {a.sent_at}')
    print(f'Status: {a.status_classification}')
    print(f'Type: {a.type}')

now = timezone.now()
print(f'\nCurrent server time: {now}')

# Check which are due
due = Announcement.objects.filter(
    status_classification='scheduled',
    sent_at__lte=now
)
print(f'\nAnnouncements due now: {due.count()}')
for a in due:
    print(f'  - {a.title} (scheduled for {a.sent_at})')
