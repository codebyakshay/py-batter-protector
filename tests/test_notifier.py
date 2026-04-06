import pytest
from unittest.mock import patch, MagicMock
from notifier import Notifier

def test_send_notification_calls_osascript():
    with patch("subprocess.run") as mock_run:
        Notifier.send_notification("Title", "Message")
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        command_list = args[0]
        # Full command string check or argument check
        full_command = " ".join(command_list)
        assert "osascript" in full_command
        assert "display notification \"Message\"" in full_command
        assert "with title \"Title\"" in full_command

def test_throttling_logic():
    notifier = Notifier()
    
    # First time alerting HIGH_BATTERY should be True
    assert notifier.should_notify("HIGH_BATTERY") is True
    
    # Second time alerting HIGH_BATTERY should be False
    assert notifier.should_notify("HIGH_BATTERY") is False
    
    # Alerting LOW_BATTERY now should be True
    assert notifier.should_notify("LOW_BATTERY") is True
    
    # Alerting None should reset
    assert notifier.should_notify(None) is False
    
    # Alerting HIGH_BATTERY again after reset should be True
    assert notifier.should_notify("HIGH_BATTERY") is True
