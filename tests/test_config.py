"""Tests for LinnyConfig serialization, defaults, and persistence."""

from linny.core.config import LinnyConfig


def test_default_config_fields():
    config = LinnyConfig()
    assert config.user_name == "Zeus"
    assert config.language == "English"
    assert config.timezone == "Asia/Manila"
    assert "code" in config.app_aliases
    assert config.tts_engine in ("edge", "pyttsx3")


def test_dict_serialization():
    config = LinnyConfig(user_name="TestUser", language="Tagalog")
    data = config.to_dict()
    assert data["user_name"] == "TestUser"
    assert data["language"] == "Tagalog"

    restored = LinnyConfig.from_dict(data)
    assert restored.user_name == "TestUser"
    assert restored.language == "Tagalog"
