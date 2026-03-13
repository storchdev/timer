#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$HOME/.config/systemd/user"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/timer"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed or not in PATH."
  exit 1
fi

UV_BIN_DIR="$(dirname "$(which uv)")"
SERVICE_PATH="$UV_BIN_DIR:${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"

mkdir -p "$SYSTEMD_DIR" "$BIN_DIR" "$CONFIG_DIR"

uv --project "$PROJECT_DIR" sync

cat >"$BIN_DIR/timer" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec uv --project "$PROJECT_DIR" run timer "\$@"
EOF
chmod +x "$BIN_DIR/timer"

cat >"$SYSTEMD_DIR/timer.service" <<EOF
[Unit]
Description=Persistent Timer Reminder Daemon
After=default.target

[Service]
Type=simple
Environment=PATH=$SERVICE_PATH
ExecStart=%h/.local/bin/timer daemon
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now timer.service

echo "Installed timer daemon service and ~/.local/bin/timer"
