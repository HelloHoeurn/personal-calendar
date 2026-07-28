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

# Calculate the target time 5 minutes from now
target_time = (now + timedelta(minutes=5)).strftime('%H:%M')

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

# 1. Check for upcoming events starting in 5 minutes
for event in today_events:
    time_str = event.get('time', '')
    # Extract start time (e.g. "08:00" from "08:00 - 11:30" or "08:00")
    start_time = time_str.split('-')[0].strip()
    
    if start_time == target_time:
        alert_msg = f"⏰ *Upcoming Activity in 5 Minutes!*\n\n• *{event['time']}*: {event['title']}"
        send_telegram_message(alert_msg)

# 2. Daily morning overview at 06:00 AM
if current_hm == "06:00":
    overview_msg = f"🌅 *Daily Schedule for {today}*\n\n"
    for event in today_events:
        overview_msg += f"• *{event['time']}*: {event['title']}\n"
    send_telegram_message(overview_msg)
