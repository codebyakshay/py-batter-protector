import pytest
from monitor import BatteryMonitor

def test_sailing_logic_high_threshold():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    alert = BatteryMonitor.check_thresholds(82, True, is_sailing=False, config=config)
    assert alert == "HIGH_BATTERY"

def test_sailing_logic_discharging_while_sailing():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    alert = BatteryMonitor.check_thresholds(81, False, is_sailing=True, config=config)
    assert alert is None

def test_sailing_logic_hit_floor_while_sailing():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    alert = BatteryMonitor.check_thresholds(50, False, is_sailing=True, config=config)
    assert alert == "LOW_BATTERY"

def test_sailing_logic_critical_floor():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    alert = BatteryMonitor.check_thresholds(30, False, is_sailing=False, config=config)
    assert alert == "LOW_BATTERY"

def test_sailing_logic_safe_zone():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    alert = BatteryMonitor.check_thresholds(60, False, is_sailing=False, config=config)
    assert alert is None
