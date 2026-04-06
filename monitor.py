import re
import subprocess
import time
import os
import json
import sys
import logging

# Local bundled helper path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BATTERY_CLI = os.path.join(PROJECT_ROOT, "bin", "battery_helper")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")
from notifier import Notifier

def setup_logger():
    logger = logging.getLogger("BatteryProtector")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
    
    # Syslog or local fallback
    log_path = "/var/log/py-battery-protector.log"
    try:
        if not os.path.exists(log_path):
            open(log_path, 'a').close()
            os.chmod(log_path, 0o644)
    except (PermissionError, OSError):
        log_path = os.path.join(PROJECT_ROOT, "py-battery-protector.log")

    fh = logging.FileHandler(log_path)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()

class HardwareController:
    """
    Interfaces with the bundled 'battery_helper' CLI to control SMC.
    Automatically drops root privileges when calling the helper, 
    as the underlying utility rejects being explicitly invoked by root.
    """
    def _run_battery_cmd(self, command: str, *args):
        # Determine the current console user
        try:
            console_user = subprocess.check_output(["stat", "-f", "%Su", "/dev/console"]).decode().strip()
        except Exception:
            console_user = None

        cmd_list = [BATTERY_CLI, command] + list(args)
        
        # If running as root but there's a console user, drop privileges
        if os.geteuid() == 0 and console_user and console_user != "root":
            cmd_list = ["sudo", "-u", console_user] + cmd_list
            
        subprocess.run(cmd_list, check=True)

    def stop_charging(self):
        """Commands the hardware to stop charging the battery (SMC bypass)."""
        try:
            self._run_battery_cmd("discharging")
            return True
        except subprocess.CalledProcessError:
            return False
            
    def start_charging(self):
        """Commands the hardware to resume charging the battery."""
        try:
            self._run_battery_cmd("charging")
            return True
        except subprocess.CalledProcessError:
            return False

    def reset_to_full(self):
        """Resets hardware to 100% maintenance mode for travel/full charge."""
        try:
            # Set internal maintain to 100 (Normal behavior)
            self._run_battery_cmd("maintain", "100")
            # Ensure it's charging
            self.start_charging()
            return True
        except subprocess.CalledProcessError:
            return False

class BatteryMonitor:
    """
    Handles battery telemetry extraction and parsing on macOS using pmset.
    """
    
    @staticmethod
    def load_config():
        """Loads configuration from config.json, or runs setup wizard if missing."""
        if not os.path.exists(CONFIG_FILE):
            return BatteryMonitor.setup_wizard()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return BatteryMonitor.setup_wizard()

    @staticmethod
    def setup_wizard():
        """Interactive one-time setup for battery thresholds."""
        print("\n" + "="*40)
        print("🔋 py-battery-protector: SETUP WIZARD")
        print("="*40)
        print("⚠️  This is a one-time configuration and will be locked once set.")
        print("-"*40)
        
        try:
            high = int(input("Enter High Ceiling (e.g. 82): ") or 82)
            sailing = int(input("Enter Sailing Floor (e.g. 50): ") or 50)
            low = int(input("Enter Low Floor (e.g. 30): ") or 30)
            
            config = {
                "high_threshold": high,
                "sailing_floor": sailing,
                "low_threshold": low
            }
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"\n✅ Configuration saved to {CONFIG_FILE}")
            print("="*40 + "\n")
            return config
        except ValueError:
            print("❌ Invalid input. Using defaults (82/50/30).")
            return {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}

    @staticmethod
    def parse_pmset_output(output: str):
        """
        Parses the raw string output from `pmset -g batt`.
        Returns (percentage: int, is_charging: bool).
        """
        # Extract percentage (e.g., "83%")
        percent_match = re.search(r'(\d+)%', output)
        if not percent_match:
            return None, False
        percentage = int(percent_match.group(1))
        
        # Determine charging status. 
        # "discharging" is the only state indicating we are losing power.
        # "charging", "AC", "finishing charge", and "AC attached" all imply 
        # that we are either gaining power or at least connected to AC.
        is_charging = "discharging" not in output.lower()
        
        return percentage, is_charging

    @classmethod
    def get_stats(cls):
        """
        Executes the pmset command and returns parsed battery stats.
        """
        try:
            output = subprocess.check_output(["pmset", "-g", "batt"]).decode("utf-8")
            return cls.parse_pmset_output(output)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback for non-macOS or missing pmset
            return None, False

    @staticmethod
    def check_thresholds(percentage: int, is_charging: bool, is_sailing: bool, config: dict):
        """
        Logic for Assisted Sailing Mode based on user config.
        """
        high = config.get("high_threshold", 82)
        sailing_floor = config.get("sailing_floor", 50)
        low = config.get("low_threshold", 30)

        if percentage >= high and is_charging:
            return "HIGH_BATTERY"
            
        if is_sailing:
            if percentage <= sailing_floor and not is_charging:
                return "LOW_BATTERY"
            return None
            
        if percentage <= low and not is_charging:
            return "LOW_BATTERY"
            
        return None

    @classmethod
    def start_monitoring(cls, interval=60):
        """
        Infinite monitoring loop with Configuration, Sailing Mode & Active hardware control.
        """
        hw = HardwareController()

        # Support for --charge flag to force 100%
        if "--charge" in sys.argv:
            print("🚀 Travel Mode: Resetting battery to normal (100%) charge...")
            if hw.reset_to_full():
                print("✅ Hardware reset. Your Mac will now charge to 100%.")
            else:
                print("❌ Failed to reset hardware. Try running with sudo.")
            return

        # Support for --reset flag to re-run one-time wizard
        if "--reset" in sys.argv:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            cls.load_config()
            return
            
        config = cls.load_config()
        
        notifier = Notifier()
        hw = HardwareController()
        is_sailing = False
        last_status = None
        
        logger.info(f"ACTIVE Sailing Mode ({config['low_threshold']}-{config['high_threshold']}-{config['sailing_floor']}) engaged...")
        
        try:
            while True:
                percent, charging = cls.get_stats()
                if percent is not None:
                    alert_type = cls.check_thresholds(percent, charging, is_sailing, config)
                    
                    # Log state updates for user clarity
                    status = "Charging/AC" if charging else "Discharging"
                    sailing_status = " [Sailing]" if is_sailing else ""
                    current_status_line = f"{percent}% - {status}{sailing_status}"
                    log_str = current_status_line
                    
                    should_print = (current_status_line != last_status)
                    
                    if alert_type and notifier.should_notify(alert_type):
                        msg = ""
                        if alert_type == "LOW_BATTERY":
                            is_sailing = False
                            hw.start_charging()
                            msg = f"Battery floor reached ({percent}%). Resuming charge automatically."
                        elif alert_type == "HIGH_BATTERY":
                            is_sailing = True
                            hw.stop_charging()
                            msg = f"Battery ceiling reached ({percent}%). Charging paused automatically (Sailing Mode)."
                        
                        if msg:
                            notifier.send_notification("py-battery-protector", msg)
                            log_str += f" | SMC ACTION: {alert_type}"
                            should_print = True
                    elif alert_type is None:
                        # Reset notification throttling when in safe zone
                        notifier.should_notify(None)
                        # If manually charging above the sailing floor, exit sailing status
                        if charging and percent > config['sailing_floor']:
                            is_sailing = False

                    if should_print:
                        logger.info(log_str)
                        last_status = current_status_line
                        
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped.")

if __name__ == "__main__":
    # Start the monitoring loop if run directly
    BatteryMonitor.start_monitoring(interval=5)
