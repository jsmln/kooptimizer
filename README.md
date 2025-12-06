# Kooptimizer

**A centralized data repository and management platform designed to digitize, streamline, and empower cooperative operations for the Lipa City Cooperatives Office.**

This system transforms legacy operations from scattered physical records and disparate digital files (Excel, Word) into a unified, secure, and analytics-driven platform. It's built to provide a single source of truth, enabling real-time updates, data-driven governance, and efficient communication.

### ✨ Key Features

* 🗃️ **Centralized Data Repository:** A unified, secure platform to store, organize, and retrieve all cooperative data.
* 📊 **Analytics & Dashboards:** Structured reports and visualizations to track cooperative performance and support informed decision-making.
* 🤖 **OCR Digitization Engine:** Integrated Optical Character Recognition (OCR) to scan and ingest physical records, dramatically reducing manual encoding time.
* 📡 **Real-Time Data Pipeline:** Allows member cooperatives to securely submit and update their information directly, ensuring data is always current.
* 📨 **Integrated Communication Tools:** Built-in SMS and Email API integration for sending bulk announcements, notifications, and alerts to cooperative officers.
* 🔒 **Robust Security:** Protected by Google ReCAPTCHA to prevent spam, bots, and automated intrusions, ensuring data integrity and platform reliability.

Overview
========

Kooptimizer is a Django-based web platform focused on cooperative and account management features, notifications, and integrations with external APIs for email, push and calendar synchronization. This README summarizes the repository structure, the API integrations used, quickstart instructions, and a short database summary. For a detailed database schema and migration instructions see `docs/database.md` and `db/schema.sql`.

API Integrations and Providers
------------------------------
- **Google APIs**: Used in the `apps/users` area for features like Google Calendar synchronization and Google reCAPTCHA verification. The project uses the `google-api-python-client` and `google-auth` libraries and expects a `service_account.json` for service account usage where applicable.
- **ReCAPTCHA (Google)**: reCAPTCHA v2/v3 verification is used for forms and authentication flows. Configure `RECAPTCHA_SECRET_KEY` in environment settings.
- **Brevo (SMTP/API)**: Email sending is done via the Brevo API (formerly Sendinblue). Environment variables include `BREVO_API_URL` and an API key. See `requirements.txt` for the HTTP client used.
- **Web Push / VAPID**: Web push notifications are supported via `django-webpush` / `pywebpush` and require VAPID keys and related settings. The app references `webpush.models.PushInformation` and related code in `apps/dashboard`.
- **Firebase Cloud Messaging (FCM)**: Mobile push notifications use FCM (Google Firebase). Logs show `fcm.googleapis.com` usage for sending device messages.

Repository Structure (important folders only)
-------------------------------------------
- `kooptimizer/` - Django project settings and WSGI/ASGI entrypoints (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- `apps/` - Main Django apps (examples: `users`, `dashboard`, `account_management`, `communications`, `cooperatives`, `core`).
- `database/` - Database artifacts: backups, migrations, updates. (Contents are often environment-specific.)
- `docs/` - Project documentation. See `docs/database.md` for DB details.
- `scripts/` - Helper scripts and stored procedure installers for database operations.
- `logs/` - Runtime logs (scheduler, workers, etc.).
- `static/`, `templates/` - Static assets and Django templates.
- `tests/` - Test suite for automated checks.

Quickstart (Windows PowerShell)
-------------------------------
Prerequisites
- Python 3.10+ (project defined in `requirements.txt` — use the version that matches this file)
- Git
- Postgres or your configured DB (see `kooptimizer/settings.py` for DB engine)

1. Clone the repo and create a virtual environment

```powershell
git clone <repo-url>
cd Kooptimizer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Create environment variables
- Copy `.env.example` (or `.env.production.template`) into `.env` and fill values such as DB connection, `SECRET_KEY`, `BREVO_API_KEY`, `RECAPTCHA_SECRET_KEY`, VAPID keys, and Google `service_account.json` path.

4. Database setup and migrations

```powershell
# create DB (example for Postgres - run externally or using your DB admin)
# psql -c "CREATE DATABASE kooptimizer;"

python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_data.json  # if fixtures exist
python manage.py createsuperuser
```

5. Run the development server

```powershell
python manage.py runserver 0.0.0.0:8000
```

Notes about API keys and files
- `service_account.json` (Google API service account) — see `service_account.json.template` for placement and format.
- `BREVO_API_KEY`, `BREVO_API_URL` — configure in `.env`.
- VAPID keys for web push — generate and store in environment variables used by `django-webpush`.

Database Summary
----------------
Kooptimizer uses Django ORM with migration-based schema management. The `database/` folder contains backups and DB-related scripts used for administration. The app also contains SQL scripts / stored procedures under `scripts/` for special DB operations. For a full schema dump, migrations, and details see `docs/database.md` and the placeholder `db/schema.sql`.

Where to find more details
- Detailed DB schema and migration notes: `docs/database.md` (committed). 
- Raw SQL export placeholder: `db/schema.sql` (committed as a starting point). 
- Developer guides, duplication analysis, and debugging notes: `docs/` (some files may be environment-specific and ignored — see `.gitignore`).

Security & Secrets
------------------
Do NOT commit `service_account.json` or production secret values. Remove secrets before pushing. A `service_account.json.template` is included to show required keys.

Contributing
------------
Follow the usual Git flow. See below for an example branch-and-push workflow.

Example: create branch, commit and push

```powershell
# create and switch to a new branch
git checkout -b DEG-dev

# stage, commit, and push changes
git add README.md docs/database.md db/schema.sql .gitignore
git commit -m "docs: update README with API integrations and add DB docs; update .gitignore"
git push -u origin DEG-dev
```

If you need further setup specifics for production (supervisors, gunicorn, nginx, SSL, systemd, containerization), ask and we will add tailored instructions.

The ultimate goal of Kooptimizer is to enhance transparency, streamline complex workflows, and foster sustainable growth for the Lipa City Cooperatives Office and its members.

---

## 📁 Project Structure

```
Kooptimizer/
├── apps/                   # Django applications
├── database/              # Database backups and migrations
│   ├── backups/          # SQL dumps and backups
│   └── updates/          # Schema updates and migrations
├── docs/                  # Documentation
│   ├── setup/            # Setup and deployment guides
│   ├── security/         # Security documentation
│   └── implementation/   # Feature implementation docs
├── frontend/             # Frontend assets (CSS, JS)
├── kooptimizer/          # Django project settings
├── logs/                 # Application logs
├── scripts/              # Utility scripts
├── static/               # Static files (CSS, images, JS)
├── stored_procedures/    # Database stored procedures
├── templates/            # HTML templates
└── tests/                # Test files
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 18
- Virtual environment

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hxrthe/Kooptimizer.git
   cd Kooptimizer
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Set up database**
   ```bash
   # See docs/setup/DATABASE_SETUP_INSTRUCTIONS.md
   ```

6. **Run the server**
   
   **Easiest way (recommended):**
   ```bash
   # Double-click START.bat or run:
   .\START.bat
   ```
   
   **Alternative methods:**
   ```bash
   # PowerShell (after enabling scripts once):
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\start_server.ps1
   
   # Command Prompt
   start_server.bat
   ```
   
   **Manual way:**
   ```bash
   .\.venv\Scripts\python.exe verify_requirements.py  # Verify packages
   .\.venv\Scripts\python.exe manage.py runserver     # Start server
   ```
   
   See **[START_SERVER.md](START_SERVER.md)** for detailed startup instructions and troubleshooting.

## 📚 Documentation

### Getting Started
- **[Quick Start](QUICK_START.txt)** - Quick reference card for starting the server
- **[Server Startup Guide](START_SERVER.md)** - Comprehensive startup and troubleshooting guide
- **[Setup Guide](docs/setup/DATABASE_SETUP_INSTRUCTIONS.md)** - Database setup and deployment

### Development & Maintenance
- **[Google API Fix](GOOGLEAPICLIENT_FIX.md)** - Fix for persistent package installation issues
- **[Feature Docs](docs/implementation/)** - Implementation guides for all features

### Security
- **[Security Guide](docs/security/SECURITY.md)** - Security best practices
- **[Credentials Reference](docs/security/CREDENTIALS_QUICK_REFERENCE.md)** - API key management

## 🧪 Testing

Run comprehensive tests to verify setup:

```bash
# Test credentials and security
python tests/test_credentials_access.py

# Test page integration
python tests/test_pages_integration.py

# Test specific features
python tests/test_optiic_api.py
```

See [tests/README.md](tests/README.md) for more details.

## 🔒 Security

All API keys and credentials are managed through environment variables using `python-decouple`. 

**Never commit `.env` files to version control.**

See [docs/security/SECURITY.md](docs/security/SECURITY.md) for security guidelines.

## 🤝 Contributing

This is a project for the Lipa City Cooperatives Office. For contributions or issues, please contact the development team.

## 📄 License

This project is proprietary software developed for the Lipa City Cooperatives Office.

---

*Last updated: December 1, 2025*
