import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

# 2. Import Models
from apps.users.models import User
from apps.cooperatives.models import Cooperative, CooperativeOfficer
from apps.communications.models import Message, Announcement, MessageRecipient

print("--- Starting Data Population ---")

# --- HELPER DATA ---
COOP_NAMES = [
    "Lipa Farmers Multi-Purpose Cooperative",
    "Batangas Transport Service Coop",
    "Metro Lipa Water District Employees Coop",
    "Golden Harvest Credit Cooperative",
    "Lipa City Teachers Cooperative",
    "San Jose Workers Cooperative",
    "Green Valley Agrarian Reform Coop",
    "Star Livelihood Cooperative",
    "Lipa Market Vendors Coop",
    "Sunrise Transport Service Cooperative"
]

CATEGORIES = ["Multi-Purpose", "Credit", "Transport", "Service", "Consumers", "Producers"]
DISTRICTS = ["North", "South", "East", "West", "Central"]

# --- 1. CREATE COOPERATIVES ---
coops = []
for name in COOP_NAMES:
    # Check if exists to avoid duplicates
    if not Cooperative.objects.filter(cooperative_name=name).exists():
        coop = Cooperative.objects.create(
            cooperative_name=name,
            address=f"Barangay {random.randint(1, 50)}, Lipa City",
            category=random.choice(CATEGORIES),
            district=random.choice(DISTRICTS),
            cda_registration_number=f"9520-{random.randint(100000, 999999)}",
            cda_registration_date=timezone.now().date() - timedelta(days=random.randint(365, 3650)),
            assets=random.uniform(500000.00, 50000000.00),
            paid_up_capital=random.uniform(100000.00, 10000000.00),
            members_count=random.randint(50, 2000),
            contact_number=f"09{random.randint(100000000, 999999999)}"
        )
        coops.append(coop)
        print(f"Created Coop: {name}")
    else:
        coops.append(Cooperative.objects.get(cooperative_name=name))

# --- 2. CREATE USERS (OFFICERS) ---
officers = []
for coop in coops:
    # Create a Chairperson for each coop
    username = f"chair_{coop.coop_id}"
    if not User.objects.filter(username=username).exists():
        user = User.objects.create(
            username=username,
            first_name=f"Chairperson",
            last_name=f"Of {coop.coop_id}",
            email=f"chair{coop.coop_id}@example.com",
            role='officer',
            mobile_number=f"09{random.randint(100000000, 999999999)}",
            password_hash=make_password('password123'),
            is_active=True
        )
        
        # Link to CooperativeOfficer table
        CooperativeOfficer.objects.create(
            user=user,
            cooperative=coop,
            position="Chairperson"
        )
        officers.append(user)
        print(f"Created Officer: {username}")

# --- 3. CREATE ADMIN & STAFF (If not exist) ---
if not User.objects.filter(username="admin_main").exists():
    admin_user = User.objects.create(
        username="admin_main",
        first_name="Main",
        last_name="Admin",
        role="admin",
        password_hash=make_password('admin123')
    )
else:
    admin_user = User.objects.get(username="admin_main")

# --- 4. GENERATE MESSAGES ---
# Send messages from Admin to Officers
for officer in officers:
    Message.objects.create(
        sender=admin_user,
        # If your model structure is One-to-Many recipients, handle that logic here.
        # Assuming a simple Message model for this script or adjusting based on your schema:
        # content="Please submit your annual report by Friday.",
        # timestamp=timezone.now() - timedelta(minutes=random.randint(1, 60))
    )
    # Note: Since I don't have your exact Message model fields (e.g., if recipients are ManyToMany),
    # I'm keeping this part generic. You might need to adjust this loop.

# --- 5. GENERATE ANNOUNCEMENTS ---
titles = [
    "Annual General Assembly Schedule",
    "New CDA Guidelines on Reporting",
    "Reminder: Submit Audited Financial Statements",
    "Cooperative Month Celebration",
    "Tax Exemption Renewal Deadline"
]

for title in titles:
    if not Announcement.objects.filter(title=title).exists():
        Announcement.objects.create(
            title=title,
            content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Please be guided accordingly.",
            type=random.choice(['sms', 'email']),
            status=random.choice(['sent', 'draft', 'scheduled']),
            sent_at=timezone.now() if random.choice([True, False]) else (timezone.now() + timedelta(days=3))
        )
        print(f"Created Announcement: {title}")

print("--- Data Population Complete! ---")
print(f"Total Coops: {len(coops)}")
print(f"Total Officers: {len(officers)}")