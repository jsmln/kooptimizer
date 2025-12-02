@echo off
REM Helper script to run Python commands in the virtual environment
REM Usage: venv-run.bat <python command>
REM Example: venv-run.bat verify_requirements.py --fix

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at .venv\Scripts\python.exe
    echo Please run this from the project root directory.
    exit /b 1
)

.venv\Scripts\python.exe %*
