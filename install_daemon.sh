#!/usr/bin/env bash

# This script creates and loads a LaunchDaemon for py-battery-protector
# It also acts as the primary CLI point for overriding / managing the daemon.

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install_daemon.sh)"
  exit 1
fi

# Get correct project directory even if invoked via symlink
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -h "$SCRIPT_PATH" ]; do
  DIR="$( cd -P "$( dirname "$SCRIPT_PATH" )" >/dev/null 2>&1 && pwd )"
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
  [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$DIR/$SCRIPT_PATH"
done
PROJECT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

TARGET_DIR="/usr/local/py-battery-protector"
PLIST_PATH="/Library/LaunchDaemons/com.battery.protector.plist"
# Use absolute system python path to prevent virtual environments from interfering
PYTHON_PATH="/usr/bin/python3"

# ==========================================
# FLAG HANDLING
# ==========================================

if [ "$1" == "--charge" ]; then
    echo "Stopping background daemon to allow 100% charge without the daemon interfering at 82%..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    echo "Initiating Travel Mode..."
    "$PYTHON_PATH" "$TARGET_DIR/monitor.py" --charge
    echo ""
    echo "⚠️  Note: The background daemon is currently paused so you can reach 100%."
    echo "Run 'sudo ./install_daemon.sh' again later when you want to resume protection!"
    exit 0
fi

if [ "$1" == "--reset" ]; then
    echo "Stopping background daemon for configuration reset..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    
    # Run setup wizard on the source tracking directory
    "$PYTHON_PATH" "${PROJECT_DIR}/monitor.py" --reset
    
    echo "Deploying new configuration..."
    cp "${PROJECT_DIR}/config.json" "$TARGET_DIR/"
    chown root:wheel "$TARGET_DIR/config.json"
    
    echo "Restarting daemon with new thresholds..."
    launchctl load -w "$PLIST_PATH"
    echo "✅ Configuration updated and daemon restarted."
    exit 0
fi

if [ "$1" == "--stop" ] || [ "$1" == "--uninstall" ]; then
    echo "Stopping and unloading daemon..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    if [ "$1" == "--uninstall" ]; then
        rm -f "$PLIST_PATH"
        echo "✅ Daemon uninstalled."
    else
        echo "✅ Daemon stopped."
    fi
    exit 0
fi

if [ -n "$1" ]; then
    echo "Unknown flag: $1"
    echo "Valid flags: --charge, --reset, --stop, --uninstall"
    exit 1
fi

# ==========================================
# DEFAULT INSTALLATION
# ==========================================

echo "Deploying to ${TARGET_DIR} to bypass macOS Desktop sandbox restrictions..."
mkdir -p "$TARGET_DIR"
cp "${PROJECT_DIR}/monitor.py" "${PROJECT_DIR}/notifier.py" "${PROJECT_DIR}/install_daemon.sh" "$TARGET_DIR/"
cp -R "${PROJECT_DIR}/bin" "$TARGET_DIR/"
if [ -f "${PROJECT_DIR}/config.json" ]; then
    cp "${PROJECT_DIR}/config.json" "$TARGET_DIR/"
else
    echo '{"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}' > "$TARGET_DIR/config.json"
fi

# Ensure correct ownership to bypass permission issues
chown -R root:wheel "$TARGET_DIR"
chmod -R 755 "$TARGET_DIR"

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.battery.protector</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${TARGET_DIR}/monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/py-battery-protector.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/py-battery-protector.log</string>
</dict>
</plist>
EOF

chmod 644 "$PLIST_PATH"
chown root:wheel "$PLIST_PATH"

echo "Loading LaunchDaemon..."
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load -w "$PLIST_PATH"

# Create a global fast CLI symlink so the user can use `sudo battery --flags` globally
ln -sf "${TARGET_DIR}/install_daemon.sh" "/usr/local/bin/battery"
chmod +x "${TARGET_DIR}/install_daemon.sh"

echo "✅ Installed! The service is now running in the background as root."
echo ""
echo "🚀 GLOBAL COMMAND ACTIVATED:"
echo "You can now run this from ANYWHERE without visiting your project directory!"
echo "Try:  sudo battery"
echo "      sudo battery --stop"
echo "      sudo battery --charge"
echo "      sudo battery --reset"
echo ""
echo "📂 View real-time background logs anytime with: tail -f /var/log/py-battery-protector.log"
