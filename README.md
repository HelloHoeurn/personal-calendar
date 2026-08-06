# personal-calendar

A personal weekly schedule (`schedule.json`) with automated Telegram reminders, delivered via a GitHub Actions cron job (`.github/workflows/daily_reminder.yml`) that runs `send_reminder.py`.

## How it works

- **`schedule.json`** — your weekly schedule, one block per day (`Monday`–`Sunday`), each with a list of `{ "time": "HH:MM - HH:MM", "title": "..." }` events. All times are Indochina Time (ICT / UTC+7).
- **`send_reminder.py`** — reads today's schedule and, each time it runs, sends a Telegram message when:
  1. It's the 06:00–06:59 ICT hour, **and** today's message hasn't already been sent (tracked in `last_sent_date.txt`) → sends the full day's schedule as a single morning overview, then marks today as sent. This is the **only** automated message per day.
  2. It's run manually (`workflow_dispatch`) → sends a test confirmation showing today's full schedule, without touching the "already sent" state.
- **`daily_reminder.yml`** — a GitHub Actions workflow that ticks every 10 minutes from 05:50–06:59 ICT, plus a `workflow_dispatch` trigger for manual testing from the Actions tab. After a successful send it commits the updated `last_sent_date.txt` back to the repo so later ticks that hour know to skip.

### Why a hour-long window + state file instead of one exact minute?

GitHub Actions scheduled workflows are **not** guaranteed to fire at their exact cron minute — in practice, runs have been observed firing 30–45+ minutes late, and occasionally getting skipped entirely under load. A single narrow window (even a few minutes wide) can miss the day's message completely if GitHub is running behind. Instead:
- The workflow ticks repeatedly across the whole 6 AM hour, so there's a good chance at least one tick lands after 6:00 even with heavy delay.
- The script itself is idempotent: it checks `last_sent_date.txt` and only sends if today's date isn't already recorded, so multiple ticks in the same hour never cause duplicate messages.

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and note the bot token.
2. Get your chat ID (e.g. message your bot, then check `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. In your repo, go to **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. **Copy `send_reminder.py`, `.github/workflows/daily_reminder.yml`, and `schedule.json` into your actual repository and commit/push them.** Editing files in this chat only changes the local copy you download — GitHub Actions only runs whatever is committed to your repo, so nothing changes on GitHub until you push.
5. The workflow runs automatically each morning. To test it immediately, go to **Actions → Daily Schedule Reminder → Run workflow**.
6. **If this is a forked repository**, GitHub disables scheduled workflows on forks by default — go to the **Actions** tab and enable workflows, then separately confirm the schedule trigger is enabled.
7. **If the repo goes 60 days with no commits**, GitHub auto-disables scheduled workflows — a small periodic commit (or re-enabling in the Actions tab) fixes this if reminders quietly stop. (The daily state-file commit itself will keep this from happening once it's running.)
8. Make sure the workflow has permission to push back to the repo: **Settings → Actions → General → Workflow permissions → Read and write permissions**. This is required for the `last_sent_date.txt` commit step.

## Editing your schedule

- Edit `schedule.json` directly — times must be `HH:MM - HH:MM` (24-hour), and events for a given day should not overlap.
- No workflow changes are needed when you add/move events — only the 6 AM overview message changes when you edit `schedule.json`.

## Notes

- GitHub Actions scheduled workflows are not guaranteed to run at the exact minute — they can be delayed by 30+ minutes during high load, which is a platform-level limitation, not a bug in this code. That's exactly what the wide window + state-file approach above is designed around.
- The overview is matched purely by day-of-week against whatever day it is when the workflow runs; the schedule doesn't need to be date-specific.
- If you ever want to force a resend on the same day (e.g. after testing), delete or edit `last_sent_date.txt` in the repo.
