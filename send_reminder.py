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

# ----------------------------------------------------
# 1. 06:00 AM Full-Day Schedule Overview
# (window is 0-4 min so exactly one 5-minute tick catches it, even if that
#  tick is a little late; the next tick at :05 won't re-match)
# ----------------------------------------------------
if now.hour == 6 and 0 <= now.minute <= 4 and not is_manual_run:
    overview_msg = f"🌅 *Good Morning! Here is your full schedule for {today}:*\n\n"
    for event in today_events:
        overview_msg += f"• *{event['time']}*: {event['title']}\n"
    send_telegram_message(overview_msg)
    message_sent = True

# ----------------------------------------------------
# 2. Automated 5-Minute Warning Before Each Activity
# (skipped if the full-day overview already fired this run, to avoid
#  double-messaging when the first event of the day starts at 06:00)
# ----------------------------------------------------
elif not is_manual_run:
    for event in today_events:
        time_str = event.get('time', '')
        start_time_str = time_str.split('-')[0].strip()
        
        try:
            event_hour, event_min = map(int, start_time_str.split(':'))
            event_time = now.replace(hour=event_hour, minute=event_min, second=0, microsecond=0)
            
            diff_seconds = (event_time - now).total_seconds()
            diff_minutes = diff_seconds / 60.0
            
            # With a 5-minute poll cadence, each event should be caught by exactly
            # one tick: the one running 0-5 minutes before it starts. A tighter
            # window here (vs. the old -5..15) avoids the same event firing twice
            # across two consecutive ticks.
            if 0 < diff_minutes <= 5:
                next_alert = f"⏰ *Up Next in 5 Minutes!*\n\n• *{event['time']}*: {event['title']}"
                send_telegram_message(next_alert)
                message_sent = True
                break
        except Exception as e:
            print(f"Error parsing event time: {e}")

# ----------------------------------------------------
# 3. MANUAL TEST RUN CONFIRMATION (Shows Code Update + Next Activity)
# ----------------------------------------------------
if is_manual_run:
    # Find the next upcoming activity for today
    next_event = None
    for event in today_events:
        time_str = event.get('time', '')
        start_time_str = time_str.split('-')[0].strip()
        try:
            event_hour, event_min = map(int, start_time_str.split(':'))
            event_time = now.replace(hour=event_hour, minute=event_min, second=0, microsecond=0)
            if event_time > now:
                next_event = event
                break
        except Exception:
            pass

    test_msg = f"✅ *Code Update Test Successful!*\n\nBot is active for *{today}*.\n"
    if next_event:
        test_msg += f"\n📌 *Next Scheduled Activity:* \n• *{next_event['time']}*: {next_event['title']}"
    else:
        test_msg += "\n🎉 No more activities scheduled for today!"
        
    send_telegram_message(test_msg)
