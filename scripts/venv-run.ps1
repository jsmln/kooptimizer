# Helper script to run Python commands in the virtual environment
# Usage: .\venv-run.ps1 <python command>
# Example: .\venv-run.ps1 verify_requirements.py --fix

$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPath)) {
    Write-Host "ERROR: Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please run this from the project root directory." -ForegroundColor Yellow
    exit 1
}

& $venvPath $args
