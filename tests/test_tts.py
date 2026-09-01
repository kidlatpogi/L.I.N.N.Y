"""Tests for VoiceEngine initialization and interruption logic."""

from linny.audio.tts import VoiceEngine


def test_voice_engine_init():
    engine = VoiceEngine(voice_name="en-PH-RosaNeural", rate=160, volume=0.9)
    assert engine.voice_name == "en-PH-RosaNeural"
    assert engine.rate == 160
    assert engine.volume == 0.9
    assert engine.is_speaking is False


def test_voice_engine_stop():
    engine = VoiceEngine()
    engine.stop()
    assert engine._interrupted is True
    assert engine.is_speaking is False
