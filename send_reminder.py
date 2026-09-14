import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import urllib.request
import urllib.parse

# ---------------------------------------------------------------------------
# Personal schedule reminder bot (Telegram + GitHub Actions)
#
# Sends two kinds of message:
#   1. A once-per-day 6 AM full-day overview (idempotent via a state file).
#   2. Optional "5 minutes before" alerts for each upcoming activity.
#
# Both are driven by schedule.json, so editing the schedule is the only thing
# you ever need to do to change what the bot says. Times are Indochina Time
# (ICT / UTC+7).
# ---------------------------------------------------------------------------

STATE_FILE = 'last_sent_date.txt'
LOCAL_TZ = ZoneInfo("Asia/Bangkok")

# How many minutes before an activity to send its heads-up alert.
ALERT_LEAD_MINUTES = 5
# Only fire a per-activity alert if this run lands within this many minutes of
# the intended alert time. GitHub Actions cron drift means "run every 5 min"
# ticks don't land exactly, so we allow a small window on either side.
ALERT_MATCH_TOLERANCE_MINUTES = 5

# Titles we never bother sending a heads-up for (routine / passive blocks).
ALERT_SKIP_TITLES = {"Sleep"}


# ----------------------------------------------------------------------------
# Load schedule + current time
# ----------------------------------------------------------------------------
with open('schedule.json', 'r') as f:
    schedule = json.load(f)

now = datetime.now(LOCAL_TZ)
today = now.strftime('%A')
today_date_str = now.strftime('%Y-%m-%d')

is_manual_run = os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'


def get_events_for(day_name):
    for day_data in schedule:
        if day_data.get('day', '').lower() == day_name.lower():
            return day_data.get('events', [])
    return []


today_events = get_events_for(today)


# ----------------------------------------------------------------------------
# Telegram
# ----------------------------------------------------------------------------
def send_telegram_message(text):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not (bot_token and chat_id):
        print("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req) as response:
        print("Message sent successfully!")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def parse_start_time(time_str):
    """'07:00 - 12:00' -> datetime today at 07:00 (ICT)."""
    start = time_str.split('-')[0].strip()
    hh, mm = map(int, start.split(':'))
    return now.replace(hour=hh, minute=mm, second=0, microsecond=0)


def build_overview():
    msg = f"\U0001F305 *Good Morning! Here is your full schedule for {today}:*\n\n"
    for event in today_events:
        msg += f"\u2022 *{event['time']}*: {event['title']}\n"
    return msg


# ----------------------------------------------------------------------------
# 1. Manual test run — show today's full schedule, don't touch daily state
# ----------------------------------------------------------------------------
if is_manual_run:
    test_msg = f"\u2705 *Bot Test Successful!*\n\nActive for *{today}*.\n\n"
    test_msg += "\U0001F4CB *Today's Full Schedule:*\n\n"
    for event in today_events:
        test_msg += f"\u2022 *{event['time']}*: {event['title']}\n"
    send_telegram_message(test_msg)
    raise SystemExit(0)


# ----------------------------------------------------------------------------
# 2. 6 AM full-day overview (once per day, idempotent via state file)
#
# GitHub Actions cron can run well after its nominal minute, so the workflow
# ticks across the whole 6 AM hour and the state file guarantees exactly one
# overview per day even if several ticks land in that hour.
# ----------------------------------------------------------------------------
already_sent_today = False
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, 'r') as f:
        already_sent_today = f.read().strip() == today_date_str

if now.hour == 6 and not already_sent_today:
    send_telegram_message(build_overview())
    with open(STATE_FILE, 'w') as f:
        f.write(today_date_str)
    print("STATE_UPDATED=true")


# ----------------------------------------------------------------------------
# 3. "5 minutes before" per-activity alerts
#
# For each event, the intended alert time is (start - ALERT_LEAD_MINUTES).
# If the current run lands within ALERT_MATCH_TOLERANCE_MINUTES of that time,
# we fire the heads-up. Because ticks are sparse (every 5 min) and the window
# is small, each activity realistically gets at most one alert. The 6 AM
# overview is the authoritative daily message; these are best-effort nudges.
# ----------------------------------------------------------------------------
for event in today_events:
    title = event['title']
    if title in ALERT_SKIP_TITLES:
        continue
    try:
        start_dt = parse_start_time(event['time'])
    except (ValueError, IndexError):
        continue

    alert_dt = start_dt - timedelta(minutes=ALERT_LEAD_MINUTES)
    delta_minutes = abs((now - alert_dt).total_seconds()) / 60.0

    if delta_minutes <= ALERT_MATCH_TOLERANCE_MINUTES:
        start_str = event['time'].split('-')[0].strip()
        alert_msg = (
            f"\u23F0 *Up next in {ALERT_LEAD_MINUTES} min* ({start_str})\n\n"
            f"\u27A1\uFE0F {title}"
        )
        send_telegram_message(alert_msg)
