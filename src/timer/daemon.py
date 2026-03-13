from __future__ import annotations

import asyncio
import os
import signal
import time
from contextlib import suppress

from timer.config import load_settings
from timer.notify import send_notifications, send_targeted_email
from timer.paths import CONFIG_DIR, PID_PATH
from timer.storage import delete_timer, due_timers, next_due_ts


class TimerDaemon:
    _MAX_SLEEP_SECONDS = 900

    def __init__(self) -> None:
        self._wake_event = asyncio.Event()
        self._stop_event = asyncio.Event()

    def _write_pid(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        PID_PATH.write_text(str(os.getpid()), encoding="utf-8")

    def _remove_pid(self) -> None:
        with suppress(FileNotFoundError):
            PID_PATH.unlink()

    async def _deliver_due(self) -> None:
        now = int(time.time())
        due = due_timers(now)
        if not due:
            return
        settings = load_settings()
        for row in due:
            duration = (
                row.duration_ms
                if row.duration_ms > 0
                else settings.notification_duration_ms
            )
            targeted_addresses = [addr for addr in row.email_targets.split(",") if addr]
            try:
                if targeted_addresses:
                    await send_targeted_email(row.message, targeted_addresses, settings)
                else:
                    await send_notifications(row.message, duration, settings)
            except Exception as exc:  # noqa: BLE001
                print(f"Failed to deliver timer {row.id}: {exc}")
            finally:
                delete_timer(row.id)

    async def _wait_for_next_or_signal(self) -> None:
        next_due = next_due_ts()
        if next_due is None:
            timeout = self._MAX_SLEEP_SECONDS
        else:
            timeout = max(0, min(next_due - int(time.time()), self._MAX_SLEEP_SECONDS))
        try:
            await asyncio.wait_for(self._wake_event.wait(), timeout=timeout)
            self._wake_event.clear()
        except TimeoutError:
            pass

    async def run(self) -> None:
        self._write_pid()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._stop_event.set)
            loop.add_signal_handler(sig, self._wake_event.set)
        loop.add_signal_handler(signal.SIGUSR1, self._wake_event.set)

        try:
            while not self._stop_event.is_set():
                await self._deliver_due()
                await self._wait_for_next_or_signal()
        finally:
            self._remove_pid()


def ping_daemon() -> bool:
    with suppress(FileNotFoundError, ProcessLookupError, ValueError, PermissionError):
        pid = int(PID_PATH.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGUSR1)
        return True
    return False
