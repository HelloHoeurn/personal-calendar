import json
import os
from datetime import datetime
import urllib.request
import urllib.parse

# Load schedule data
with open('schedule.json', 'r') as f:
    schedule = json.load(f)

# Get today's day of the week (e.g., "Monday")
today = datetime.now().strftime('%A')

# Find today's events
today_events = None
for day_data in schedule:
    if day_data.get('day').lower() == today.lower():
        today_events = day_data.get('events', [])
        break

# Format message
if today_events:
    message = f"📅 *Schedule for {today}*\n\n"
    for event in today_events:
        message += f"• *{event['time']}*: {event['title']}\n"
else:
    message = f"📅 *Schedule for {today}*\n\nNo scheduled events today!"

# Get bot secrets from environment variables
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_CHAT_ID')

# Send message to Telegram
if bot_token and chat_id:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req) as response:
        print("Message sent successfully!")
else:
    print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
