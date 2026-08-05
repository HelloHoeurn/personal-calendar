# personal-calendar

A personal weekly schedule (`schedule.json`) with automated Telegram reminders, delivered via a GitHub Actions cron job (`.github/workflows/daily_reminder.yml`) that runs `send_reminder.py`.

## How it works

- **`schedule.json`** — your weekly schedule, one block per day (`Monday`–`Sunday`), each with a list of `{ "time": "HH:MM - HH:MM", "title": "..." }` events. All times are Indochina Time (ICT / UTC+7).
- **`send_reminder.py`** — reads today's schedule and, each time it runs, checks the clock and sends a Telegram message when:
  1. It's the 06:00–06:04 ICT window → sends the full day's schedule as a single morning overview. This is the **only** automated message per day — there are no per-event "coming up" alerts.
  2. It's run manually (`workflow_dispatch`) → sends a test confirmation showing today's full schedule, without counting as the automated daily send.
- **`daily_reminder.yml`** — a GitHub Actions workflow that runs `send_reminder.py` on a handful of ticks clustered around 6 AM ICT, plus a `workflow_dispatch` trigger for manual testing from the Actions tab.

### Why several cron ticks instead of one?

GitHub Actions scheduled workflows are not guaranteed to fire at an exact minute — runs can be delayed by several minutes, especially during high load. Pinning the daily send to a single cron minute means a delayed run silently skips the day entirely. Instead, the workflow fires on nine 1-minute ticks from 05:55–06:04 ICT; the script's own window check (`06:00 ≤ time ≤ 06:04`) only actually sends on the ticks inside that window, and a late run still lands inside it instead of missing it.

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and note the bot token.
2. Get your chat ID (e.g. message your bot, then check `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. In your repo, go to **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. The workflow runs automatically each morning. To test it immediately, go to **Actions → Daily Schedule Reminder → Run workflow**.
5. **If this is a forked repository**, GitHub disables scheduled workflows on forks by default — go to the **Actions** tab and enable workflows, then separately confirm the schedule trigger is enabled.
6. **If the repo goes 60 days with no commits**, GitHub auto-disables scheduled workflows — a small periodic commit (or re-enabling in the Actions tab) fixes this if reminders quietly stop.
7. This schedule only runs a handful of times per day, so Actions usage is negligible either way.

## Editing your schedule

- Edit `schedule.json` directly — times must be `HH:MM - HH:MM` (24-hour), and events for a given day should not overlap.
- No workflow changes are needed when you add/move events — only the 6 AM overview message changes when you edit `schedule.json`.

## Notes

- GitHub Actions scheduled workflows are not guaranteed to run at the exact minute — they can be delayed by a few minutes during high load, which is a platform-level limitation, not a bug in this code.
- The overview is matched purely by day-of-week against whatever day it is when the workflow runs; the schedule doesn't need to be date-specific.
