@echo off
REM Batch file to send scheduled announcements
REM Run this every minute using Windows Task Scheduler

cd /d "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"
call .venv\Scripts\activate.bat
python manage.py send_scheduled_announcements >> logs\scheduled_announcements.log 2>&1
