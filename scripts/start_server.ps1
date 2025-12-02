# Kooptimizer Development Server Startup Script (PowerShell)
# This script activates the virtual environment, verifies requirements, and starts the Django server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kooptimizer Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv .venv" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] Activating virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"
# Check if activation succeeded by verifying VIRTUAL_ENV is set
if (-not $env:VIRTUAL_ENV) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "The venv exists but couldn't be activated." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Gray
Write-Host ""

Write-Host "[2/3] Verifying requirements..." -ForegroundColor Green
& "./.venv/Scripts/python.exe" verify_requirements.py --fix
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Some packages may be missing" -ForegroundColor Yellow
    Write-Host "You can continue, but some features might not work" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Do you want to continue anyway? (y/n)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 1
    }
}
Write-Host ""

Write-Host "[3/3] Starting Django development server..." -ForegroundColor Green
Write-Host ""
Write-Host "Server will be available at: " -NoNewline
Write-Host "http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& "./.venv/Scripts/python.exe" manage.py runserver

# If server stops, keep window open
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Server stopped" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
