from __future__ import annotations

from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "timer"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
DB_PATH = CONFIG_DIR / "timers.sqlite3"
PID_PATH = CONFIG_DIR / "daemon.pid"
