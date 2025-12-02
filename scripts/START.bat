@echo off
REM Simple one-liner to start the Kooptimizer server
REM This bypasses PowerShell execution policy issues

echo Starting Kooptimizer Development Server...
echo.

REM Run using venv Python directly (no activation needed)
.venv\Scripts\python.exe verify_requirements.py --fix
if errorlevel 1 (
    echo.
    echo WARNING: Some packages may be missing
    pause
)

echo.
echo Starting Django server at http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.

.venv\Scripts\python.exe manage.py runserver
