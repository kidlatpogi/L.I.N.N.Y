"""Tests for SmartDeviceManager offline handling and color mapping."""

from linny.core.config import LinnyConfig
from linny.integrations.smart_home import COLOR_PRESETS, SmartDeviceManager


def test_color_presets_coverage():
    assert "red" in COLOR_PRESETS
    assert "blue" in COLOR_PRESETS
    assert "green" in COLOR_PRESETS
    assert "violet" in COLOR_PRESETS


def test_offline_device_graceful():
    # Placeholder IP should not raise exceptions
    config = LinnyConfig(smart_bulb_ip="<BULB_IP>")
    mgr = SmartDeviceManager(config)
    assert mgr.is_connected() is False

    # Calling actions on offline device returns False safely without crash
    res = mgr.turn_on()
    assert res is False
    mgr.close()
