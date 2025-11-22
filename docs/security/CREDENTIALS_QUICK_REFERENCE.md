# Quick Reference: Credentials Management

## Daily Development

### Starting Development
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run server (credentials auto-loaded from .env)
python manage.py runserver
```

### Adding New API Credentials

1. **Add to `.env`**:
```bash
NEW_API_KEY=your-secret-key-here
```

2. **Add to `settings.py`**:
```python
from decouple import config

NEW_API_KEY = config('NEW_API_KEY')
```

3. **Add to `.env.example`**:
```bash
NEW_API_KEY=your-api-key-here
```

4. **Use in your code**:
```python
from django.conf import settings

api_key = settings.NEW_API_KEY
```

## Running Tests

```bash
# Test all credentials are secure
python test_credentials_access.py

# Test credentials work in pages
python test_pages_integration.py

# Check Django deployment security
python manage.py check --deploy
```

## Current API Keys Location

All credentials are in **`.env`** file (never commit this!):

```
c:\Users\Noe Gonzales\Downloads\System\Kooptimizer\.env
```

### Available Credentials

| Service | Environment Variable | Used In |
|---------|---------------------|---------|
| Database | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | All views |
| Django Secret | `SECRET_KEY` | Sessions, CSRF |
| ReCAPTCHA | `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY` | Login page |
| IPROG SMS | `IPROG_SMS_API_TOKEN`, `IPROG_SMS_API_URL` | SMS announcements, OTP |
| Brevo Email | `BREVO_API_KEY`, `BREVO_SENDER_EMAIL` | Email announcements, account mgmt |
| Ticketmaster | `TICKETMASTER_API_KEY` | Optional events |
| OPTIIC OCR | `OPTIIC_API_KEY` | Optional OCR |

## Troubleshooting

### "Config Error: Missing KEY_NAME"
- ✅ **Solution**: Add the key to `.env` file
- Check `.env.example` for required format

### "Can't import settings"
- ✅ **Solution**: Ensure Django setup is correct
```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()
from django.conf import settings
```

### "Database connection failed"
- ✅ **Check**: `.env` has correct database credentials
- ✅ **Verify**: PostgreSQL is running on port 5432
- ✅ **Test**: `python manage.py check`

## Production Deployment

1. **Copy production template**:
```bash
copy .env.production.template .env.production
```

2. **Generate new SECRET_KEY**:
```bash
python generate_secret_key.py
```

3. **Update production values** in `.env.production`

4. **Enable security settings**:
```bash
DJANGO_DEBUG=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
```

5. **Run security check**:
```bash
python manage.py check --deploy
```

## Security Best Practices

✅ **DO**:
- Keep `.env` in `.gitignore`
- Use different credentials for dev/prod
- Rotate API keys regularly
- Use strong passwords
- Run `test_credentials_access.py` before commits

❌ **DON'T**:
- Commit `.env` file
- Share `.env` via email/chat
- Use production credentials in development
- Hardcode any credentials in code
- Store API keys in documentation

## Need Help?

- Read: `SECURITY.md` for detailed guidelines
- Check: `TEST_RESULTS.md` for test results
- Run: `python test_credentials_access.py` to verify setup

---
*Quick Reference v1.0 - November 22, 2025*
