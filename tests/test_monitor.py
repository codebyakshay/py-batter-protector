import pytest
from monitor import BatteryMonitor

def test_parse_discharging():
    output = " -InternalBattery-0 (id=6881379)        83%; discharging; 10:46 remaining present: true"
    percentage, charging = BatteryMonitor.parse_pmset_output(output)
    assert percentage == 83
    assert charging is False

def test_parse_charging():
    output = " -InternalBattery-0 (id=6881379)        45%; charging; 1:20 remaining present: true"
    percentage, charging = BatteryMonitor.parse_pmset_output(output)
    assert percentage == 45
    assert charging is True

def test_parse_full_ac():
    output = " -InternalBattery-0 (id=6881379)        100%; AC; AC attached; present: true"
    percentage, charging = BatteryMonitor.parse_pmset_output(output)
    assert percentage == 100
    assert charging is True

def test_parse_finishing_charge():
    output = " -InternalBattery-0 (id=6881379)        99%; finishing charge; 0:05 remaining present: true"
    percentage, charging = BatteryMonitor.parse_pmset_output(output)
    assert percentage == 99
    assert charging is True

def test_check_thresholds_low():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    # 15% and discharging -> should alert (LOW)
    alert = BatteryMonitor.check_thresholds(15, False, False, config)
    assert alert == "LOW_BATTERY"

def test_check_thresholds_high():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    # 82% and charging -> should alert (HIGH)
    alert = BatteryMonitor.check_thresholds(82, True, False, config)
    assert alert == "HIGH_BATTERY"

def test_check_thresholds_safe():
    config = {"high_threshold": 82, "sailing_floor": 50, "low_threshold": 30}
    # 50% and charging -> no alert
    alert = BatteryMonitor.check_thresholds(50, True, False, config)
    assert alert is None
