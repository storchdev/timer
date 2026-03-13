from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime

from prettytable import PrettyTable

from timer.config import ensure_settings_file
from timer.daemon import TimerDaemon, ping_daemon
from timer.storage import add_timer, delete_timer, init_db, list_timers, shift_timer
from timer.timeparse import parse_human_datetime, parse_human_offset_seconds


def _ping_or_warn() -> None:
    if not ping_daemon():
        print(
            "Warning: timer daemon did not respond. Check `systemctl --user status timer.service`."
        )


def _format_countdown(seconds: int) -> str:
    sign = "" if seconds >= 0 else "-"
    remaining = abs(seconds)
    hours, rem = divmod(remaining, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{sign}{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{sign}{minutes}m {secs}s"
    return f"{sign}{secs}s"


def _parse_email_targets(value: str) -> str:
    unique_targets: list[str] = []
    for chunk in value.split(","):
        target = chunk.strip()
        if not target or target in unique_targets:
            continue
        unique_targets.append(target)
    return ",".join(unique_targets)


def cmd_add(args: argparse.Namespace) -> int:
    due = parse_human_datetime(args.when)
    now = datetime.now()
    if due <= now:
        raise ValueError("Parsed time is not in the future.")
    email_targets = ""
    if args.email:
        email_targets = _parse_email_targets(args.email)
        if not email_targets:
            raise ValueError("--email must include at least one email address.")
    timer_id = add_timer(
        args.message,
        int(due.timestamp()),
        int(args.duration),
        email_targets,
    )
    _ping_or_warn()
    print(f"Added timer {timer_id}: '{args.message}' at {due}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    deleted = 0
    for timer_id in args.ids:
        if delete_timer(timer_id):
            deleted += 1
    _ping_or_warn()
    print(f"Deleted {deleted}/{len(args.ids)} timer(s).")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    rows = list_timers()
    table = PrettyTable(["ID", "Message", "Due", "In", "Duration(ms)"])
    now_ts = int(datetime.now().timestamp())
    for row in rows:
        due_dt = datetime.fromtimestamp(row.due_ts)
        table.add_row(
            [
                row.id,
                row.message,
                due_dt.strftime("%Y-%m-%d %H:%M:%S"),
                _format_countdown(row.due_ts - now_ts),
                row.duration_ms,
            ]
        )
    if rows:
        print(table)
    else:
        print("No timers scheduled.")
    return 0


def cmd_add_time(args: argparse.Namespace) -> int:
    offset = parse_human_offset_seconds(args.offset)
    if not shift_timer(args.id, offset):
        raise ValueError(f"Timer {args.id} not found.")
    _ping_or_warn()
    print(f"Added {offset} seconds to timer {args.id}.")
    return 0


def cmd_remove_time(args: argparse.Namespace) -> int:
    offset = parse_human_offset_seconds(args.offset)
    if not shift_timer(args.id, -offset):
        raise ValueError(f"Timer {args.id} not found.")
    _ping_or_warn()
    print(f"Removed {offset} seconds from timer {args.id}.")
    return 0


def cmd_daemon(_: argparse.Namespace) -> int:
    daemon = TimerDaemon()
    asyncio.run(daemon.run())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent desktop timer/reminder")
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a timer")
    add_p.add_argument("message", help="Reminder message")
    add_p.add_argument("when", help="Human-readable date/time")
    add_p.add_argument(
        "-t",
        "--duration",
        type=int,
        default=0,
        help="Notify timeout in ms. 0 uses settings.json default.",
    )
    add_p.add_argument(
        "--email",
        default="",
        help="Comma-separated email addresses for targeted email delivery.",
    )
    add_p.set_defaults(func=cmd_add)

    del_p = sub.add_parser("delete", help="Delete timer(s) by id")
    del_p.add_argument("ids", nargs="+", type=int)
    del_p.set_defaults(func=cmd_delete)

    list_p = sub.add_parser("list", help="List pending timers")
    list_p.set_defaults(func=cmd_list)

    add_time = sub.add_parser("add-time", help="Add offset to timer due time")
    add_time.add_argument("id", type=int)
    add_time.add_argument("offset", help="Human-readable offset like '15 minutes'")
    add_time.set_defaults(func=cmd_add_time)

    remove_time = sub.add_parser(
        "remove-time", help="Remove offset from timer due time"
    )
    remove_time.add_argument("id", type=int)
    remove_time.add_argument("offset", help="Human-readable offset like '10 minutes'")
    remove_time.set_defaults(func=cmd_remove_time)

    daemon_p = sub.add_parser("daemon", help="Run timer daemon")
    daemon_p.set_defaults(func=cmd_daemon)

    return parser


def main() -> None:
    ensure_settings_file()
    init_db()
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        code = 2
    raise SystemExit(code)
