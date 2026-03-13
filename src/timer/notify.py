from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from timer.config import Settings


async def send_notifications(
    message: str, duration_ms: int, settings: Settings
) -> None:
    for method in settings.notification_methods:
        if method == "notify-send":
            await _notify_send(message, duration_ms)
        elif method == "email":
            await _email_notify(message, settings)


async def send_targeted_email(
    message: str, target_addresses: list[str], settings: Settings
) -> None:
    await asyncio.to_thread(
        _send_targeted_email_sync, message, target_addresses, settings
    )


async def _notify_send(message: str, duration_ms: int) -> None:
    proc = await asyncio.create_subprocess_exec(
        "notify-send",
        "-t",
        str(duration_ms),
        "Timer Reminder",
        message,
    )
    await proc.wait()


def _send_email_sync(message: str, settings: Settings) -> None:
    if not settings.email_address:
        print("Email method configured, but email_address is empty.")
        return
    if not settings.email_username or not settings.email_password:
        print("Email method configured, but username/password are missing.")
        return

    email = EmailMessage()
    email["From"] = settings.email_address
    email["To"] = settings.email_address
    email["Subject"] = "Timer Reminder"
    email.set_content(message)

    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.email_username, settings.email_password)
        smtp.send_message(email)


async def _email_notify(message: str, settings: Settings) -> None:
    await asyncio.to_thread(_send_email_sync, message, settings)


def _send_targeted_email_sync(
    message: str, target_addresses: list[str], settings: Settings
) -> None:
    if not settings.email_address:
        print("Targeted email requested, but email_address is empty.")
        return
    if not settings.email_username or not settings.email_password:
        print("Targeted email requested, but username/password are missing.")
        return

    unique_targets: list[str] = []
    for raw in target_addresses:
        addr = raw.strip()
        if not addr or addr in unique_targets:
            continue
        unique_targets.append(addr)

    cc_targets = [addr for addr in unique_targets if addr != settings.email_address]

    email = EmailMessage()
    email["From"] = settings.email_address
    email["To"] = settings.email_address
    if cc_targets:
        email["Cc"] = ", ".join(cc_targets)
    email["Subject"] = "Timer Reminder"
    email.set_content(message)

    with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.email_username, settings.email_password)
        smtp.send_message(email)
