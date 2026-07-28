import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import urllib.request
import urllib.parse

# Load schedule data
with open('schedule.json', 'r') as f:
    schedule = json.load(f)

# Get current time in Indochina Time (ICT / UTC+7)
local_tz = ZoneInfo("Asia/Bangkok")
now = datetime.now(local_tz)
today = now.strftime('%A')
current_hm = now.strftime('%H:%M')

# Get today's events from JSON
today_events = []
for day_data in schedule:
    if day_data.get('day').lower() == today.lower():
        today_events = day_data.get('events', [])
        break

# Function to send Telegram message
def send_telegram_message(text):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }).encode('utf-8')
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req) as response:
            print("Message sent successfully!")
    else:
        print("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

is_manual_run = os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'
message_sent = False

# 1. Check for upcoming events starting in 1 to 10 minutes (handles GitHub schedule delays)
for event in today_events:
    time_str = event.get('time', '')
    start_time_str = time_str.split('-')[0].strip()
    
    try:
        # Parse event start time for today
        event_hour, event_min = map(int, start_time_str.split(':'))
        event_time = now.replace(hour=event_hour, minute=event_min, second=0, microsecond=0)
        
        # Calculate time difference in minutes
        diff_minutes = (event_time - now).total_seconds() / 60
        
        # Alert if the activity starts within 1 to 10 minutes from now
        if 0 <= diff_minutes <= 10:
            alert_msg = f"⏰ *Upcoming Activity starting soon!*\n\n• *{event['time']}*: {event['title']}"
            send_telegram_message(alert_msg)
            message_sent = True
    except Exception as e:
        print(f"Error parsing event time: {e}")

# 2. Daily morning overview around 06:00 AM (06:00 to 06:10 AM window)
if 6 == now.hour and 0 <= now.minute <= 10:
    overview_msg = f"🌅 *Daily Schedule for {today}*\n\n"
    for event in today_events:
        overview_msg += f"• *{event['time']}*: {event['title']}\n"
    send_telegram_message(overview_msg)
    message_sent = True

# 3. If manually triggered and no event matched, send confirmation
if is_manual_run and not message_sent:
    test_msg = f"✅ *Manual Run Test*\n\nBot is working! Today is *{today}*. Next activity check completed successfully."
    send_telegram_message(test_msg)
