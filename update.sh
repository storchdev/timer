#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "No git repository found at $PROJECT_DIR"
  exit 1
fi

if ! git -C "$PROJECT_DIR" pull --ff-only; then
  echo "Warning: git pull failed, continuing with local code"
fi

echo "Syncing project dependencies..."
uv --project "$PROJECT_DIR" sync

echo "Reloading user systemd units..."
systemctl --user daemon-reload

echo "Restarting timer.service (non-blocking)..."
systemctl --user restart --no-block timer.service

echo "Update complete: pulled latest code and restarted timer.service"
