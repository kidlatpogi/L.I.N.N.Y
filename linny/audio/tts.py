"""
Dual-Engine Text-to-Speech (TTS) subsystem for Linny.
Primary Engine: Microsoft Edge Neural TTS (Natural, High-Fidelity)
Fallback Engine: Pyttsx3 SAPI5 (100% Offline)
Audio Output: Pygame Mixer with thread-safe playback, cancellation, and buffer streaming.
"""

from __future__ import annotations

import asyncio
import io
import os
import tempfile
import threading
import time
from typing import Callable, Optional

import edge_tts
import pyttsx3

from ..core.events import EventBus, EventType
from ..core.logger import get_logger

logger = get_logger("tts")

# Popular Edge Neural voices
EDGE_VOICES = {
    "English (Philippines - Rosa)": "en-PH-RosaNeural",
    "English (Philippines - James)": "en-PH-JamesNeural",
    "English (US - Jenny)": "en-US-JennyNeural",
    "English (US - Aria)": "en-US-AriaNeural",
    "English (US - Guy)": "en-US-GuyNeural",
    "Filipino (Philippines - Blessica)": "fil-PH-BlessicaNeural",
    "Filipino (Philippines - Angelo)": "fil-PH-AngeloNeural",
}


class VoiceEngine:
    """Enterprise-grade, dual-engine TTS coordinator with instant cancellation."""

    def __init__(
        self,
        voice_name: str = "en-PH-RosaNeural",
        rate: int = 150,
        volume: float = 1.0,
        preferred_engine: str = "edge",
    ) -> None:
        self.voice_name = voice_name
        self.rate = rate
        self.volume = max(0.0, min(1.0, volume))
        self.preferred_engine = preferred_engine
        self.is_speaking = False
        self._interrupted = False
        self._playback_lock = threading.Lock()
        self._event_bus = EventBus()
        self._pygame_initialized = False

        self._init_audio_backend()
        logger.info(f"VoiceEngine initialized (Voice: {self.voice_name}, Preferred: {self.preferred_engine})")

    def _init_audio_backend(self) -> None:
        """Initialize Pygame Mixer for smooth MP3 playback."""
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._pygame_initialized = True
        except Exception as e:
            logger.warning(f"Could not initialize Pygame mixer: {e}")
            self._pygame_initialized = False

    def set_voice(self, voice_name: str) -> None:
        self.voice_name = voice_name
        logger.info(f"TTS voice updated to: {voice_name}")

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def stop(self) -> None:
        """Instantly stop any active speech synthesis and audio playback."""
        self._interrupted = True
        if self._pygame_initialized:
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass
        self.is_speaking = False
        logger.info("Speech playback interrupted")

    def _speak_edge(self, text: str) -> bool:
        """Synthesize via Edge TTS and play audio using Pygame mixer."""
        temp_file_path: Optional[str] = None
        try:
            # Generate unique temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                temp_file_path = tf.name

            # Run edge_tts communicate
            async def _generate() -> None:
                communicate = edge_tts.Communicate(text, self.voice_name)
                await communicate.save(temp_file_path)

            asyncio.run(_generate())

            if self._interrupted or not os.path.exists(temp_file_path):
                return False

            if not self._pygame_initialized:
                self._init_audio_backend()

            if self._pygame_initialized:
                import pygame
                pygame.mixer.music.load(temp_file_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() and not self._interrupted:
                    time.sleep(0.05)

                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                return not self._interrupted
            return False

        except Exception as e:
            logger.warning(f"Edge TTS synthesis error: {e}. Falling back to pyttsx3.")
            return False
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass

    def _speak_pyttsx3(self, text: str) -> bool:
        """Offline fallback synthesis using SAPI5 pyttsx3."""
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)

            # Try to select female voice
            voices = engine.getProperty("voices")
            for v in voices:
                if any(k in v.name.lower() for k in ["zira", "female", "natural"]):
                    engine.setProperty("voice", v.id)
                    break
            else:
                if voices:
                    engine.setProperty("voice", voices[0].id)

            if not self._interrupted:
                engine.say(text)
                engine.runAndWait()
            try:
                engine.stop()
            except Exception:
                pass
            return True
        except Exception as e:
            logger.error(f"pyttsx3 fallback error: {e}")
            return False

    def speak(self, text: str, callback: Optional[Callable[[], None]] = None) -> None:
        """Speak the given text asynchronously in a dedicated worker thread."""
        if not text or not text.strip():
            if callback:
                callback()
            return

        def _worker() -> None:
            with self._playback_lock:
                self._interrupted = False
                self.is_speaking = True
                self._event_bus.publish(EventType.SPEECH_STARTED, {"text": text})
                self._event_bus.publish(EventType.STATE_CHANGED, {"state": "speaking", "description": text[:60]})
                logger.info(f"Speaking: {text[:80]}...")

                success = False
                if self.preferred_engine == "edge":
                    success = self._speak_edge(text)

                if not success and not self._interrupted:
                    logger.info("Using offline Pyttsx3 speech engine")
                    self._speak_pyttsx3(text)

                self.is_speaking = False
                self._event_bus.publish(EventType.SPEECH_FINISHED, {})
                self._event_bus.publish(EventType.STATE_CHANGED, {"state": "listening", "description": "Ready"})

                if callback and not self._interrupted:
                    try:
                        callback()
                    except Exception as err:
                        logger.error(f"TTS completion callback error: {err}")

        speech_thread = threading.Thread(target=_worker, daemon=True, name="LinnyTTSWorker")
        speech_thread.start()
