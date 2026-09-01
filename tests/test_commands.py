"""Unit tests for voice commands, wake word matching, and intent execution."""

from unittest.mock import MagicMock, patch
import pytest

from linny.core.config import LinnyConfig
from linny.core.assistant import LinnyAssistant


@pytest.fixture
def assistant():
    cfg = LinnyConfig(smart_bulb_enabled=False)
    ast = LinnyAssistant(cfg)
    # Mock voice synthesis so tests don't play audio
    ast.voice.speak = MagicMock()
    ast.smart_home.turn_on = MagicMock(return_value=True)
    ast.smart_home.turn_off = MagicMock(return_value=True)
    ast.smart_home.set_brightness = MagicMock(return_value=True)
    ast.smart_home.set_color = MagicMock(return_value=True)
    ast.power.media_play_pause = MagicMock()
    ast.power.media_next = MagicMock()
    ast.power.media_prev = MagicMock()
    ast.power.media_volume_up = MagicMock()
    ast.power.media_volume_down = MagicMock()
    ast.power.media_mute = MagicMock()
    ast.launcher.launch = MagicMock(return_value=(True, "Opening Brave."))
    yield ast
    ast.stop()


def test_wake_word_extraction(assistant):
    has_wake, cmd = assistant.is_wake_word_present("Hey Linny open brave")
    assert has_wake is True
    assert "open brave" in cmd.lower()

    has_wake, cmd = assistant.is_wake_word_present("Hey open spotify")
    assert has_wake is True
    assert "open spotify" in cmd.lower()

    has_wake, cmd = assistant.is_wake_word_present("open brave")
    assert has_wake is True


def test_app_launch_intent(assistant):
    assistant.execute_command("open brave")
    assistant.launcher.launch.assert_called_with("brave")

    assistant.execute_command("launch spotify")
    assistant.launcher.launch.assert_called_with("spotify")


def test_weather_intent(assistant):
    assistant.execute_command("what is the weather")
    assistant.voice.speak.assert_called()
    spoken_text = assistant.voice.speak.call_args[0][0]
    assert "celsius" in spoken_text.lower() or "degrees" in spoken_text.lower() or "weather" in spoken_text.lower()


def test_time_and_date_intent(assistant):
    assistant.execute_command("what time is it")
    assistant.voice.speak.assert_called()
    spoken_text = assistant.voice.speak.call_args[0][0]
    assert "it is" in spoken_text.lower() or "m" in spoken_text.lower()

    assistant.execute_command("what is the date today")
    spoken_text = assistant.voice.speak.call_args[0][0]
    assert "today is" in spoken_text.lower() or "202" in spoken_text


def test_schedule_intent(assistant):
    assistant.execute_command("what's on my schedule")
    assistant.voice.speak.assert_called()


def test_smart_lights_intent(assistant):
    assistant.execute_command("lights on")
    assistant.smart_home.turn_on.assert_called()

    assistant.execute_command("turn off the light")
    assistant.smart_home.turn_off.assert_called()

    assistant.execute_command("set brightness to 75%")
    assistant.smart_home.set_brightness.assert_called_with(75)

    assistant.execute_command("set color to blue")
    assistant.smart_home.set_color.assert_called_with("blue")


def test_media_controls_intent(assistant):
    assistant.execute_command("pause music")
    assistant.power.media_play_pause.assert_called()

    assistant.execute_command("resume music")
    assistant.power.media_play_pause.assert_called()

    assistant.execute_command("next track")
    assistant.power.media_next.assert_called()

    assistant.execute_command("previous song")
    assistant.power.media_prev.assert_called()

    assistant.execute_command("volume up")
    assistant.power.media_volume_up.assert_called()

    assistant.execute_command("volume down")
    assistant.power.media_volume_down.assert_called()

    assistant.execute_command("mute audio")
    assistant.power.media_mute.assert_called()
