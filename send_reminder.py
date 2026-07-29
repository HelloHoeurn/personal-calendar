import json
import os
from datetime import datetime
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

# Get today's events from JSON
today_events = []
for day_data in schedule:
    if day_data.get('day').lower() == today.lower():
        today_events = day_data.get('events', [])
        break

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

# 1. Check for events starting around now (-10 mins to +20 mins window)
for event in today_events:
    time_str = event.get('time', '')
    start_time_str = time_str.split('-')[0].strip()
    
    try:
        event_hour, event_min = map(int, start_time_str.split(':'))
        event_time = now.replace(hour=event_hour, minute=event_min, second=0, microsecond=0)
        
        # Minutes until the event starts
        diff_minutes = (event_time - now).total_seconds() / 60
        
        # Catch events starting within 20 mins or started up to 10 mins ago
        if -10 <= diff_minutes <= 20:
            alert_msg = f"⏰ *Upcoming Activity Alert!*\n\n• *{event['time']}*: {event['title']}"
            send_telegram_message(alert_msg)
            message_sent = True
    except Exception as e:
        print(f"Error parsing event time: {e}")

# 2. Morning overview (around 06:00 AM ICT)
if 5 <= now.hour <= 6 and not message_sent and not is_manual_run:
    overview_msg = f"🌅 *Daily Schedule for {today}*\n\n"
    for event in today_events:
        overview_msg += f"• *{event['time']}*: {event['title']}\n"
    send_telegram_message(overview_msg)
    message_sent = True

# 3. Confirmation for manual test run
if is_manual_run and not message_sent:
    test_msg = f"✅ *Manual Run Test*\n\nBot is active! Today is *{today}*. Connection to Telegram is fully functional."
    send_telegram_message(test_msg)
