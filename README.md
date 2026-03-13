# timer

Persistent Linux desktop reminders with `notify-send` and optional email.

## Features

- Human-readable times via `parsedatetime` (e.g. `tomorrow 9am`, `in 45 minutes`)
- Persistent queue in `~/.config/timer/timers.sqlite3`
- Async daemon that sleeps until next due timer (no 1-second polling loop)
- Notification methods from config (`notify-send`, `email`)
- Table output for `list` with `prettytable`

## Install

From this project directory:

```bash
./install.sh
```

This installs:

- `~/.local/bin/timer` wrapper command
- user service `~/.config/systemd/user/timer.service`
- enabled/running systemd user daemon (`timer daemon`)

## Usage

```bash
timer add "Take a break" "in 25 minutes"
timer add "Team standup" "tomorrow 9:30am" -t 8000
timer add "Send report" "today 5pm" --email "boss@company.com,team@company.com"
timer list
timer delete 1
timer add-time 2 "10 minutes"
timer remove-time 2 "5 minutes"
```

`-t/--duration` is milliseconds for `notify-send` timeout.

- `-t 0` means use persistent default from `settings.json`.

## Config

Config file: `~/.config/timer/settings.json`

Default content:

```json
{
  "notification_duration_ms": 5000,
  "notification_methods": "notify-send",
  "email_address": "",
  "email_username": "",
  "email_password": "",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

`notification_methods` is a comma-separated list. Supported values: `notify-send,email`.

If `email` is included in `notification_methods`, the app sends from `email_address` to itself on port `587` with STARTTLS.

If you pass `--email` to `timer add`, that timer bypasses normal notification methods and sends a targeted email: `email_address` is the `To` recipient and the comma-separated `--email` addresses are deduplicated and added to `Cc`.

## Update

```bash
./update.sh
```

This does a `git pull --ff-only`, syncs dependencies, reloads systemd user units, and restarts `timer.service`.
