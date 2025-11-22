# Kooptimizer Tests

This folder contains all test files for the Kooptimizer project.

## 🧪 Test Files

### Credentials & Security Tests
- `test_credentials_access.py` - Verifies all API keys and database credentials are properly configured
- `test_pages_integration.py` - Tests credentials work across all pages and services

### Feature Tests
- `test_optiic_api.py` - Tests OPTIIC OCR API integration
- `test_announcement_view.py` - Tests announcement viewing functionality
- `test_draft_endpoint.py` - Tests draft announcement endpoints
- `test_view_endpoint.py` - Tests announcement detail endpoints

### Utility Tests
- `analyze_test_failures.py` - Analyzes and reports on test failures
- `test_failures_impact_report.py` - Generates impact assessment for failed tests
- `check_db_size.py` - Checks database size and storage information
- `list_urls.py` - Lists all URLs in the application

## 🚀 Running Tests

### Run All Credential Tests
```bash
python tests/test_credentials_access.py
```

### Run Integration Tests
```bash
python tests/test_pages_integration.py
```

### Run Specific Feature Tests
```bash
# Test OPTIIC OCR
python tests/test_optiic_api.py

# Test announcements
python tests/test_announcement_view.py
python tests/test_draft_endpoint.py
```

### Run All Tests
```bash
python tests/test_credentials_access.py
python tests/test_pages_integration.py
```

## ✅ Expected Results

All tests should pass with:
- **Credentials Test**: 100% success rate (33/33 tests)
- **Integration Test**: 100% success rate (39/39 tests)

## 📊 Test Coverage

- ✅ Database credentials
- ✅ API keys (ReCAPTCHA, IPROG SMS, Brevo Email, OPTIIC OCR, Ticketmaster)
- ✅ Django core settings
- ✅ Security settings
- ✅ Email service integration
- ✅ SMS service integration
- ✅ OTP service
- ✅ Database connections
- ✅ Session management
- ✅ CSRF protection

## 📝 Adding New Tests

When adding new test files:
1. Name them with `test_` prefix
2. Include docstrings explaining what's being tested
3. Update this README with the new test information

---
*Last updated: November 22, 2025*
