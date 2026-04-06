# 🔋 py-battery-protector

A robust, background Python-based utility to monitor and manage macOS battery health. Designed particularly for Apple Silicon MacBooks, this tool acts as a lightweight alternative to utilities like AlDente, preventing the battery from holding a continuous 100% charge when constantly plugged in.

By strictly managing the internal SMC (System Management Controller) state, **py-battery-protector** enforces "Sailing Mode," ensuring healthy, optimal battery degradation paths and preventing micro-charge cycles.

## ✨ Features

- **The "Sailing Mode" Philosophy (30-82-50):**
  - Automatically commands the hardware to **stop charging at 82%**.
  - Sails straight down to **50%** before ever allowing power to charge the battery back up.
  - Throws critical notifications if your battery dips below **30%** so you don't wear out the bottom-end cells.
  - _Note: All thresholds are fully customizable._
- **System-Level Persistence**: Fully deployed out of the macOS sandbox to `/usr/local/py-battery-protector` and wrapped cleanly as a `.plist` `launchd` background daemon. It survives sleep/wake, reboots, and terminal closures natively.
- **Root-to-Desktop Notifications**: Accurately fires native macOS `osascript` visual notifications from the background root daemon directly into the active user's desktop session.
- **Zero-Friction Global CLI**: Includes a globally injected `battery` OS command for instant intervention from any terminal directory.

## 🚀 Installation & Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/py-battery-protector.git
   cd py-battery-protector
   ```

2. **Deploy the Daemon:**
   Because it has to interface with native macOS hardware instructions (`SMC`), the installation logic requires root permissions.

   ```bash
   sudo ./install_daemon.sh
   ```

3. **Configure your thresholds:**
   During your first installation, a Setup Wizard will appear to lock in your preferred Sailing thresholds. Once set, the daemon pushes to the background autonomously forever.

## 🖥️ The Global `battery` CLI

Once installed, the installer automatically symlinks a native, global command. From any path on your terminal, you can interact with the daemon:

| Command                    | Description                                                                                                                                                                          |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `sudo battery`             | Reinstalls or manually restarts the underlying daemon.                                                                                                                               |
| `sudo battery --charge`    | **"Travel Mode"**. Completely disables the custom daemon protection and forces your Mac to standard 100% charging behavior. Ideal for when you're jumping on a plane in a few hours. |
| `sudo battery --stop`      | Stops both the background polling service and detaches the SMC hook.                                                                                                                 |
| `sudo battery --reset`     | Pauses the daemon and throws you back into the Setup Wizard to redefine your Sailing thresholds.                                                                                     |
| `sudo battery --uninstall` | Fully uninstalls the plist configurations, removing the system daemon completely.                                                                                                    |

## 🗄️ Monitoring & Logging

You don't need a clunky UI taking up RAM. You can inspect the live decision loop of the daemon natively through the central system logs:

```bash
tail -f /var/log/py-battery-protector.log
```

## 🧠 Core Architecture

- `monitor.py`: The core autonomous state machine implementing the Sailing logic algorithm.
- `notifier.py`: Wraps `osascript` to target the active console user and aggressively block repetitive notification spam.
- `install_daemon.sh`: The brains behind the deployment system—routing configurations, symlinks, and system logs safely around the macOS Desktop TCC sandbox restrictions.

## ⚖️ License

MIT License. Free to fork and optimize.
