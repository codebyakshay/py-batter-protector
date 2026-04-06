import subprocess

class Notifier:
    """
    Handles native macOS notifications and alert throttling.
    """
    
    def __init__(self):
        self.last_alert_type = None

    def should_notify(self, alert_type: str):
        """
        Throttling logic: only notify if the alert_type has changed from the last one sent.
        If alert_type is None, it indicates we are back in the safe zone (reset state).
        """
        if alert_type == self.last_alert_type:
            return False
            
        self.last_alert_type = alert_type
        
        # If we just moved back to None (safe zone), we don't send a notification 
        # saying "everything is fine", we just reset our ability to alert again 
        # when the threshold is hit.
        if alert_type is None:
            return False
            
        return True

    @staticmethod
    def send_notification(title: str, message: str):
        """
        Sends a native macOS notification using osascript.
        Routes to the active console user if running as a root daemon.
        """
        # Using double quotes for AppleScript string literals. 
        # Note: we aren't sanitizing input here for brevity as it's internally generated.
        script = f'display notification "{message}" with title "{title}"'
        
        try:
            # Try to get the current console user to show UI when running as root daemon
            console_user = subprocess.check_output(["stat", "-f", "%Su", "/dev/console"]).decode().strip()
            if console_user and console_user != "root":
                command = ["sudo", "-u", console_user, "osascript", "-e", script]
            else:
                command = ["osascript", "-e", script]
        except Exception:
            command = ["osascript", "-e", script]
        
        try:
            subprocess.run(command, check=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fail silently if osascript is unavailable
            pass

if __name__ == "__main__":
    # Test notification
    Notifier.send_notification("py-battery-protector", "Native notifications are active!")
