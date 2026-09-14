# personal-calendar (PP)

A personal weekly schedule (`schedule.json`) with automated Telegram reminders,
delivered via a GitHub Actions cron job (`.github/workflows/daily_reminder.yml`)
that runs `send_reminder.py`. Rebuilt around the **PP** routine (work 07:00–12:00
/ 13:00–16:00 ICT, wake 05:00, Mon–Sat identical, lighter Sunday).

## What it sends

All times are Indochina Time (ICT / UTC+7).

1. **6 AM full-day overview** — once per day, the authoritative message. Lists
   the whole day's schedule. Idempotent: a state file (`last_sent_date.txt`)
   ensures exactly one overview per day even though the workflow ticks several
   times across the 6 AM hour to survive GitHub's cron drift.
2. **"5 minutes before" activity alerts** — a short heads-up before each
   activity starts (e.g. *"Up next in 5 min (12:00) ➡️ Lunch break"*). These are
   best-effort nudges driven by the same `schedule.json`; `Sleep` blocks are
   skipped. Each alert cron fires around the right minute and the script only
   sends if the run lands within a small tolerance window of the target time.
3. **Manual test** (`workflow_dispatch`) — sends a confirmation with today's
   full schedule, without touching the daily "already sent" state.

## Files

- **`schedule.json`** — your weekly schedule, one block per day
  (`Monday`–`Sunday`), each with `{ "time": "HH:MM - HH:MM", "title": "..." }`
  events. Editing this is the only thing you need to do to change what the bot
  says (except: adding a brand-new start time means adding a matching alert cron
  in the workflow — see below).
- **`send_reminder.py`** — reads today's events and sends the overview and/or
  alerts depending on the current ICT time.
- **`.github/workflows/daily_reminder.yml`** — the cron schedule + manual
  trigger, and a step that commits `last_sent_date.txt` after a successful
  overview send.

## Why a window + state file instead of one exact minute?

GitHub Actions scheduled workflows are **not** guaranteed to fire at their exact
cron minute — runs have been observed firing 30–45+ minutes late, and
occasionally skipped under load. So the 6 AM overview ticks repeatedly across the
whole hour, and the script is idempotent (checks `last_sent_date.txt`) so
multiple ticks never double-send. The per-activity alerts accept a small
tolerance window for the same reason; because ticks are sparse, each activity
realistically gets at most one alert.

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and note the
   bot token.
2. Get your chat ID (message your bot, then check
   `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. In your repo: **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. **Copy `send_reminder.py`, `.github/workflows/daily_reminder.yml`, and
   `schedule.json` into your repository and commit/push them.** GitHub Actions
   only runs what's committed — editing local copies changes nothing on GitHub
   until you push.
5. It runs automatically. To test now: **Actions → Daily Schedule Reminder →
   Run workflow**.
6. **Forked repo?** GitHub disables scheduled workflows on forks by default —
   go to the **Actions** tab and enable them.
7. **60 days with no commits** auto-disables scheduled workflows. The daily
   state-file commit keeps this from happening once it's running; if reminders
   quietly stop, re-enable in the Actions tab.
8. Give the workflow push permission: **Settings → Actions → General → Workflow
   permissions → Read and write permissions** (needed for the
   `last_sent_date.txt` commit). The workflow also declares
   `permissions: contents: write` for the same reason.

## Editing your schedule

- Edit `schedule.json` directly — times must be `HH:MM - HH:MM` (24-hour), and
  events for a given day should not overlap.
- Moving an existing event: no workflow change needed; both the overview and its
  alert follow the new time automatically **as long as** an alert cron already
  covers 5 minutes before that start time.
- Adding a **new start time** that no existing cron covers: add a
  `- cron: 'MM HH * * *'` line (UTC = ICT − 7h, for 5 minutes before the start)
  to `daily_reminder.yml`, or just rely on the 6 AM overview for that item.

## Tuning

In `send_reminder.py`:
- `ALERT_LEAD_MINUTES` — how many minutes before an activity to alert (default 5).
- `ALERT_MATCH_TOLERANCE_MINUTES` — how close a run must land to fire (default 5).
- `ALERT_SKIP_TITLES` — titles to never alert on (default: `Sleep`).

## Notes

- The schedule is matched by day-of-week against whatever day it is when the
  workflow runs; it doesn't need to be date-specific.
- To force a resend of the overview on the same day (e.g. after testing), delete
  or edit `last_sent_date.txt` in the repo.
