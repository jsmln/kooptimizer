@echo off
REM Kooptimizer Development Server Startup Script
REM This script activates the virtual environment, verifies requirements, and starts the Django server

echo ========================================
echo Kooptimizer Development Server
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first with: python -m venv .venv
    echo.
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated: %VIRTUAL_ENV%
echo.

echo [2/3] Verifying requirements...
.venv\Scripts\python.exe verify_requirements.py --fix
if errorlevel 1 (
    echo.
    echo WARNING: Some packages may be missing
    echo You can continue, but some features might not work
    echo.
    choice /C YN /M "Do you want to continue anyway"
    if errorlevel 2 exit /b 1
)
echo.

echo [3/3] Starting Django development server...
echo.
echo Server will be available at: http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

.venv\Scripts\python.exe manage.py runserver

REM If server stops, keep window open
echo.
echo ========================================
echo Server stopped
echo ========================================
pause
