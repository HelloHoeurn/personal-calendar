# personal-calendar

A personal weekly schedule (`schedule.json`) with automated Telegram reminders, delivered via a GitHub Actions cron job (`.github/workflows/daily_reminder.yml`) that runs `send_reminder.py`.

## How it works

- **`schedule.json`** — your weekly schedule, one block per day (`Monday`–`Sunday`), each with a list of `{ "time": "HH:MM - HH:MM", "title": "..." }` events. All times are Indochina Time (ICT / UTC+7).
- **`send_reminder.py`** — reads today's schedule and, each time it runs, checks the clock and sends a Telegram message when:
  1. It's the 06:00–06:04 ICT window → sends the full day's schedule as a morning overview.
  2. Otherwise, an event is starting in the next 1–5 minutes → sends a "coming up" alert for that event.
  3. It's run manually (`workflow_dispatch`) → sends a test confirmation showing the next upcoming activity, without spamming the normal alerts.
- **`daily_reminder.yml`** — a GitHub Actions workflow that runs `send_reminder.py` **every 5 minutes, all day**, plus a `workflow_dispatch` trigger for manual testing from the Actions tab.

### Why every 5 minutes instead of one cron per event?

GitHub Actions scheduled workflows are not guaranteed to fire at an exact minute — runs can be delayed by several minutes, especially during high load. An earlier version of this workflow tried to schedule one `cron` line per event (23 of them), each with only a single valid minute — if GitHub delayed that one run even slightly, the check window was missed entirely and the reminder silently never went out. Polling every 5 minutes and letting the script's own time-window math (`0 < minutes_until_start <= 5`) decide what to send is far more resilient to that delay, since a late run still lands inside the window.

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and note the bot token.
2. Get your chat ID (e.g. message your bot, then check `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. In your repo, go to **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. The workflow runs automatically every 5 minutes. To test it immediately, go to **Actions → Daily Schedule Reminder → Run workflow**.
5. **If this is a forked repository**, GitHub disables scheduled workflows on forks by default — go to the **Actions** tab and enable workflows, then separately confirm the schedule trigger is enabled.
6. **If the repo goes 60 days with no commits**, GitHub auto-disables scheduled workflows — a small periodic commit (or re-enabling in the Actions tab) fixes this if reminders quietly stop.
7. Running every 5 minutes uses ~288 workflow runs/day. This is free and unlimited on **public** repositories. On a **private** repo it counts against your monthly Actions minutes (roughly 90–100 min/day at a few seconds per run), so keep an eye on usage or make the repo public if the schedule content isn't sensitive.

## Editing your schedule

- Edit `schedule.json` directly — times must be `HH:MM - HH:MM` (24-hour), and events for a given day should not overlap.
- No workflow changes are needed when you add/move events — the every-5-minute poll picks up anything in `schedule.json` automatically, as long as event start times are on a 5-minute boundary (e.g. `06:40`, not `06:42`).

## Notes

- GitHub Actions scheduled workflows are not guaranteed to run at the exact minute — they can be delayed by a few minutes during high load, which is a platform-level limitation, not a bug in this code.
- Reminders are matched purely by time-of-day against whatever day it is when the workflow runs; the schedule doesn't need to be day-specific.
