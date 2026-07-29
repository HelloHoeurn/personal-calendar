# personal-calendar

A personal weekly schedule (`schedule.json`) with automated Telegram reminders, delivered via a GitHub Actions cron job (`.github/workflows/daily_reminder.yml`) that runs `send_reminder.py`.

## How it works

- **`schedule.json`** — your weekly schedule, one block per day (`Monday`–`Sunday`), each with a list of `{ "time": "HH:MM - HH:MM", "title": "..." }` events. All times are Indochina Time (ICT / UTC+7).
- **`send_reminder.py`** — reads today's schedule and sends a Telegram message when:
  1. It's 06:00–06:15 ICT → sends the full day's schedule as a morning overview.
  2. Otherwise, an event is starting within the next 15 minutes (or started up to 5 minutes ago) → sends a "coming up" alert for that event.
  3. It's run manually (`workflow_dispatch`) → sends a test confirmation showing the next upcoming activity, without spamming the normal alerts.
- **`daily_reminder.yml`** — a GitHub Actions workflow with one `cron` entry per event start time across the week (converted to UTC), plus a `workflow_dispatch` trigger for manual testing from the Actions tab.

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and note the bot token.
2. Get your chat ID (e.g. message your bot, then check `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. In your repo, go to **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. The workflow runs automatically on the schedule. To test it immediately, go to **Actions → Daily Schedule Reminder → Run workflow**.

## Editing your schedule

- Edit `schedule.json` directly — times must be `HH:MM - HH:MM` (24-hour), and events for a given day should not overlap.
- If you add a new event at a start time that doesn't already have a reminder, add a matching `cron` entry to `daily_reminder.yml` (event time in ICT, minus 7 hours, for the UTC cron value), so it gets a "5 minutes before" alert.

## Notes

- GitHub Actions scheduled workflows are not guaranteed to run at the exact minute — they can be delayed by a few minutes during high load, which is a platform-level limitation, not a bug in this code.
- Reminders are matched purely by time-of-day against whatever day it is when the workflow runs; the cron schedule doesn't need to be day-specific.
