from __future__ import annotations

import json
from dataclasses import dataclass

from timer.paths import CONFIG_DIR, SETTINGS_PATH


@dataclass(slots=True)
class Settings:
    notification_duration_ms: int
    notification_methods: list[str]
    email_address: str
    email_username: str
    email_password: str
    smtp_server: str
    smtp_port: int


DEFAULT_SETTINGS = {
    "notification_duration_ms": 5000,
    "notification_methods": "notify-send",
    "email_address": "",
    "email_username": "",
    "email_password": "",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
}

SUPPORTED_METHODS = {"notify-send", "email"}


def _parse_methods(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = value.replace(" ", ",").split(",")
    methods = [item.strip() for item in raw if item.strip()]
    unique_methods: list[str] = []
    for method in methods:
        if method not in SUPPORTED_METHODS:
            continue
        if method not in unique_methods:
            unique_methods.append(method)
    return unique_methods or ["notify-send"]


def ensure_settings_file() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        try:
            current = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if not isinstance(current, dict):
                current = {}
        except json.JSONDecodeError:
            current = {}
        merged = DEFAULT_SETTINGS | current
        SETTINGS_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        return
    SETTINGS_PATH.write_text(json.dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8")


def load_settings() -> Settings:
    ensure_settings_file()
    data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    merged = DEFAULT_SETTINGS | data
    return Settings(
        notification_duration_ms=int(merged["notification_duration_ms"]),
        notification_methods=_parse_methods(merged["notification_methods"]),
        email_address=str(merged["email_address"]),
        email_username=str(merged["email_username"]),
        email_password=str(merged["email_password"]),
        smtp_server=str(merged["smtp_server"]),
        smtp_port=int(merged["smtp_port"]),
    )
