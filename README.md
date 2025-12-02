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
