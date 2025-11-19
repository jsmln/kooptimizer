# Instructions for Setting Up Scheduled Announcement Sending

## Overview
Scheduled announcements are automatically sent when their scheduled time is reached. This is handled by a management command that should run periodically.

## Setup on Windows

### Method 1: Windows Task Scheduler (Recommended)

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create a New Task**
   - Click "Create Basic Task" in the Actions panel
   - Name: "Send Scheduled Announcements"
   - Description: "Automatically sends scheduled announcements from Kooptimizer"

3. **Set Trigger**
   - When: Daily
   - Recur every: 1 day
   - Click "Next"

4. **Set Action**
   - Action: "Start a program"
   - Program/script: `C:\Users\Noe Gonzales\Downloads\System\Kooptimizer\send_scheduled_announcements.bat`
   - Click "Next"

5. **Advanced Settings**
   - After creating, right-click the task → Properties
   - Go to "Triggers" tab → Edit trigger
   - Check "Repeat task every" → Select "1 minute"
   - For a duration of: "Indefinitely"
   - Click OK

6. **Verify**
   - Right-click the task → "Run" to test
   - Check `logs\scheduled_announcements.log` for output

### Method 2: Manual Testing

Run the command manually to test:

```bash
cd "C:\Users\Noe Gonzales\Downloads\System\Kooptimizer"
.venv\Scripts\activate
python manage.py send_scheduled_announcements
```

## How It Works

1. **Scheduling an Announcement**
   - User creates an announcement
   - Selects "Schedule Send" option
   - Chooses date and time
   - Announcement is saved with `status_classification = 'scheduled'`

2. **Automatic Sending**
   - Task Scheduler runs the command every minute
   - Command checks for announcements where:
     - `status_classification = 'scheduled'`
     - `sent_at <= current_time`
   - Sends the announcement via SMS (or email when implemented)
   - Updates `status_classification = 'sent'`

3. **Logging**
   - All activity is logged to `logs\scheduled_announcements.log`
   - Check this file for debugging

## Troubleshooting

### Announcements not sending?

1. Check if Task Scheduler task is running:
   - Open Task Scheduler
   - Find "Send Scheduled Announcements"
   - Check "Last Run Time" and "Last Run Result"

2. Check the log file:
   ```
   logs\scheduled_announcements.log
   ```

3. Run manually to see errors:
   ```bash
   python manage.py send_scheduled_announcements
   ```

### SMS not sending?

- Verify SMS service credentials in settings
- Check SMS service is properly configured
- Review error messages in the log

## Email Support

Email sending is not yet implemented. When ready:
1. Uncomment email service code in `send_scheduled_announcements.py`
2. Configure email settings in Django settings
3. Test email functionality

## Production Deployment

For production servers:
- Use system service (systemd on Linux)
- Use cron job on Unix-like systems
- Ensure proper logging and monitoring
- Set up alerts for failed sends
