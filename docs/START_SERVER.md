# Starting the Kooptimizer Development Server

## Quick Start (Recommended)

### Method 1: Using START.bat (No Setup Required!)

**This is the EASIEST method - works immediately:**

```bash
# Double-click the file in Explorer, or run from terminal:
.\START.bat
```

This bypasses PowerShell execution policy issues and works out of the box!

### Method 2: Using PowerShell scripts

**First time only** - Enable PowerShell script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Then run:**

```powershell
.\start_server.ps1
```

### Method 3: Using Command Prompt scripts

```cmd
start_server.bat
```

### Method 4: Manual startup

**Using venv Python directly (no activation needed):**
```powershell
# Navigate to project directory
cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"

# Use venv Python explicitly
.\.venv\Scripts\python.exe verify_requirements.py
.\.venv\Scripts\python.exe manage.py runserver
```

**Or activate venv first:**
```powershell
# Navigate to project directory
cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Verify requirements (recommended before every start)
python verify_requirements.py

# Start the Django development server
python manage.py runserver
```

**Windows (Command Prompt):**
```cmd
cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"
.venv\Scripts\activate.bat
python verify_requirements.py
python manage.py runserver
```

## Troubleshooting

### Issue: PowerShell script execution is disabled

**Error Message:**
```
.\start_server.ps1 cannot be loaded because running scripts is disabled on this system.
```

**Solution:**

**Option 1 (Easiest):** Use START.bat instead:
```bash
.\START.bat
```

**Option 2:** Enable PowerShell scripts (one time only):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then you can run `.\start_server.ps1`

### Issue: "googleapiclient module not found" after hard refresh

**Root Cause:** Using the wrong Python (global instead of virtual environment).

**Solutions:**

1. **Use the startup scripts (recommended):**
   ```powershell
   .\START.bat
   ```

2. **Always verify your virtual environment is activated:**
   ```powershell
   # You should see (.venv) at the start of your terminal prompt
   # If not, activate it:
   .\.venv\Scripts\Activate.ps1
   ```

3. **Run the requirements verification script:**
   ```powershell
   .\.venv\Scripts\python.exe verify_requirements.py
   ```
   
   This will check all packages and offer to install missing ones.

4. **Auto-fix mode (installs missing packages automatically):**
   ```powershell
   .\.venv\Scripts\python.exe verify_requirements.py --fix
   ```

4. **Manual package installation:**
   ```powershell
   pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib
   ```

5. **Reinstall all requirements:**
   ```powershell
   pip install -r requirements.txt
   ```

6. **Hard server restart:**
   - Stop the server (Ctrl+C)
   - Deactivate and reactivate the virtual environment:
     ```powershell
     deactivate
     .\.venv\Scripts\Activate.ps1
     ```
   - Verify requirements: `python verify_requirements.py`
   - Start server: `python manage.py runserver`

### Issue: Packages installed but still showing errors

**Possible causes and fixes:**

1. **Wrong Python environment:**
   ```powershell
   # Check which Python is being used
   python -c "import sys; print(sys.executable)"
   
   # Should show: C:\Users\Noe Gonzales\Downloads\System\Kooptimizer\.venv\Scripts\python.exe
   ```

2. **Package installed globally instead of in virtual environment:**
   ```powershell
   # Ensure venv is activated (you should see (.venv) in prompt)
   # Then reinstall in the venv:
   pip install --force-reinstall google-api-python-client
   ```

3. **Multiple Python installations conflict:**
   ```powershell
   # Use the explicit path to the venv Python
   .\.venv\Scripts\python.exe -m pip install google-api-python-client
   ```

### Issue: Hard refresh causes server to lose packages

**This is now fixed with the following improvements:**

1. **Import error handling:** The `apps/users/views.py` now gracefully handles missing Google API packages and shows clear warnings instead of crashing.

2. **Startup checks:** Django now checks for critical packages on startup and displays warnings if they're missing.

3. **Runtime protection:** Google Calendar sync is automatically skipped if packages are unavailable, allowing the rest of the application to work normally.

**What this means for you:**
- The app won't crash if Google API packages are missing
- You'll see clear warnings in the console about what needs to be installed
- Other features continue to work even if Google Calendar sync is unavailable

## Best Practices

### Daily Development Workflow

1. **Start your day:**
   ```powershell
   cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"
   .\.venv\Scripts\Activate.ps1
   python verify_requirements.py
   python manage.py runserver
   ```

2. **After pulling new code:**
   ```powershell
   pip install -r requirements.txt  # Update dependencies
   python manage.py migrate          # Apply database changes
   python manage.py runserver
   ```

3. **If you experience package issues:**
   ```powershell
   python verify_requirements.py --fix
   ```

### Server Restart After Code Changes

Django's auto-reloader should handle most code changes automatically. However, if you need to manually restart:

- **Soft restart:** Press `Ctrl+C` once, then run `python manage.py runserver` again
- **Hard restart:** Press `Ctrl+C`, deactivate/reactivate venv, verify requirements, then start server

### Monitoring Server Health

When the server starts, check the console for:

1. **✓ Google API client is available** - Google Calendar integration is ready
2. **⚠ WARNING: google-api-python-client is not installed!** - Need to install packages

If you see warnings, run: `python verify_requirements.py --fix`

## Common Commands Reference

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Verify/fix requirements
python verify_requirements.py          # Interactive mode
python verify_requirements.py --fix    # Auto-install mode

# Django management
python manage.py runserver             # Start development server
python manage.py runserver 8080        # Start on different port
python manage.py migrate               # Apply database migrations
python manage.py makemigrations        # Create new migrations
python manage.py createsuperuser       # Create admin user

# Package management
pip list                               # Show installed packages
pip install -r requirements.txt        # Install all requirements
pip freeze > requirements.txt          # Update requirements file
pip show google-api-python-client      # Show package details

# Testing
python manage.py test                  # Run all tests
python test_comprehensive_functionality.py  # Run comprehensive tests
```

## Production Considerations

Before deploying to production:

1. Set `DEBUG=False` in environment variables
2. Configure proper `ALLOWED_HOSTS`
3. Set up proper `SECRET_KEY`
4. Use a production WSGI server (not `runserver`)
5. Ensure all requirements are installed in the production environment

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- Project README: `README.md`
- Testing Guide: `QUICK_TESTING_GUIDE.md`
