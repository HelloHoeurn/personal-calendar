import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.request
import urllib.parse

STATE_FILE = 'last_sent_date.txt'

# Load schedule data
with open('schedule.json', 'r') as f:
    schedule = json.load(f)

# Get current time in Indochina Time (ICT / UTC+7)
local_tz = ZoneInfo("Asia/Bangkok")
now = datetime.now(local_tz)
today = now.strftime('%A')
today_date_str = now.strftime('%Y-%m-%d')

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

def build_overview():
    msg = f"🌅 *Good Morning! Here is your full schedule for {today}:*\n\n"
    for event in today_events:
        msg += f"• *{event['time']}*: {event['title']}\n"
    return msg

is_manual_run = os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'

# ----------------------------------------------------
# 1. 6 AM Full-Day Schedule Overview (the only automated message per day)
#
# GitHub Actions scheduled runs can be delayed well beyond their nominal
# cron minute (observed delays of 30-45+ minutes), so instead of trying to
# hit one exact narrow minute, this checks a whole hour-long window
# (06:00-06:59 ICT) AND tracks whether today's message already went out via
# a small state file. The workflow ticks several times during that hour;
# whichever tick is the first to actually run sends the message and marks
# today as done, so later ticks in the same hour are safely skipped and you
# still get exactly one message, even under GitHub's scheduling drift.
# ----------------------------------------------------
if not is_manual_run:
    already_sent_today = False
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            already_sent_today = f.read().strip() == today_date_str

    if now.hour == 6 and not already_sent_today:
        send_telegram_message(build_overview())
        with open(STATE_FILE, 'w') as f:
            f.write(today_date_str)
        # Signal to the workflow that it should commit the updated state file.
        print("STATE_UPDATED=true")

# ----------------------------------------------------
# 2. MANUAL TEST RUN CONFIRMATION (shows the full schedule on demand,
#    without touching the "already sent today" state)
# ----------------------------------------------------
if is_manual_run:
    test_msg = f"✅ *Code Update Test Successful!*\n\nBot is active for *{today}*.\n\n"
    test_msg += "📋 *Today's Full Schedule:*\n\n"
    for event in today_events:
        test_msg += f"• *{event['time']}*: {event['title']}\n"
    send_telegram_message(test_msg)
