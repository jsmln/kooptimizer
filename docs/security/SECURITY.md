# Security Guidelines for Kooptimizer

## Overview
This document outlines the security practices implemented in Kooptimizer to protect sensitive credentials and API keys.

## Environment Variables

### Why We Use python-decouple
- **Never hardcode credentials** in `settings.py`
- **Type casting** for booleans, integers, and CSV lists
- **Default values** only for non-sensitive settings
- **Consistent API** across development and production

### Required Environment Variables

All sensitive credentials are stored in `.env` file (never committed to git).

#### Django Core
```bash
SECRET_KEY=your-unique-secret-key-here
DJANGO_DEBUG=False  # Set to False in production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

#### Database
```bash
DB_NAME=kooptimizer_db2
DB_USER=your_db_user
DB_PASSWORD=your_strong_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

#### Third-Party APIs
```bash
# ReCAPTCHA
RECAPTCHA_SITE_KEY=your-site-key
RECAPTCHA_SECRET_KEY=your-secret-key

# IPROG SMS
IPROG_SMS_API_TOKEN=your-api-token

# Brevo Email
BREVO_API_KEY=your-brevo-api-key
BREVO_SENDER_EMAIL=verified@yourdomain.com
BREVO_SENDER_NAME=Your App Name

# Optional Services
OPTIIC_API_KEY=your-ocr-key
TICKETMASTER_API_KEY=your-ticketmaster-key
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your real credentials
# NEVER commit .env to version control
```

### 3. Generate Secret Key
```python
# Run this in Django shell or Python console
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 4. Verify .gitignore
Ensure `.env` files are listed in `.gitignore`:
```
*.env
.env
.env.local
.env.production
```

## Production Deployment Checklist

- [ ] Set `DJANGO_DEBUG=False`
- [ ] Use strong, unique `SECRET_KEY`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Use strong database passwords
- [ ] Rotate API keys regularly
- [ ] Enable HTTPS/SSL certificates
- [ ] Review Django security checklist: `python manage.py check --deploy`

## Security Best Practices

### DO ✅
- Store all secrets in `.env` file
- Use `python-decouple` for environment variables
- Keep `.env` in `.gitignore`
- Use different credentials for dev/staging/production
- Regularly rotate API keys and passwords
- Use environment variables in CI/CD pipelines

### DON'T ❌
- Commit `.env` file to git
- Hardcode credentials in code
- Share `.env` file via email/chat
- Use production credentials in development
- Store credentials in documentation
- Use default/example credentials in production

## Incident Response

If credentials are accidentally exposed:

1. **Immediately rotate** all exposed credentials
2. **Revoke** compromised API keys
3. **Change** database passwords
4. **Generate** new Django SECRET_KEY
5. **Review** git history and remove sensitive data
6. **Notify** team members and stakeholders

## Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/5.2/topics/security/)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [python-decouple Documentation](https://github.com/HBNetwork/python-decouple)

## Contact

For security concerns, contact the development team immediately.
