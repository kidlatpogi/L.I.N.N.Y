"""
Speech Recognition (STT) subsystem for Linny.
Handles microphone streaming, background noise adaptation, phrase detection,
and wake-word / speech-to-text processing.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import speech_recognition as sr

from ..core.events import EventBus, EventType
from ..core.logger import get_logger

logger = get_logger("stt")


class SpeechListener:
    """Robust, non-blocking background speech listener with echo cancellation lock."""

    def __init__(
        self,
        on_command_callback: Callable[[str], None],
        microphone_index: Optional[int] = None,
    ) -> None:
        self.on_command_callback = on_command_callback
        self.microphone_index = microphone_index
        self.is_listening = False
        self.is_muted = False

        self.recognizer = sr.Recognizer()
        self._audio_source: Optional[sr.Microphone] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_bus = EventBus()

        # Optimize recognizer thresholds for responsive voice control
        self.recognizer.pause_threshold = 0.6
        self.recognizer.non_speaking_duration = 0.3
        self.recognizer.dynamic_energy_threshold = True

    def toggle_mute(self) -> bool:
        """Toggle microphone mute status."""
        self.is_muted = not self.is_muted
        state_str = "muted" if self.is_muted else "listening"
        logger.info(f"Microphone status: {'MUTED' if self.is_muted else 'ACTIVE'}")
        self._event_bus.publish(EventType.MUTE_TOGGLED, {"is_muted": self.is_muted})
        self._event_bus.publish(EventType.STATE_CHANGED, {"state": state_str, "description": "Microphone muted" if self.is_muted else "Listening"})
        return self.is_muted

    def set_muted(self, muted: bool) -> None:
        self.is_muted = muted
        state_str = "muted" if self.is_muted else "listening"
        self._event_bus.publish(EventType.MUTE_TOGGLED, {"is_muted": self.is_muted})
        self._event_bus.publish(EventType.STATE_CHANGED, {"state": state_str, "description": "Microphone muted" if self.is_muted else "Listening"})

    def start(self) -> bool:
        """Initialize microphone and start background listening loop."""
        if self.is_listening:
            return True

        self._stop_event.clear()
        try:
            mic_kwargs = {}
            if self.microphone_index is not None:
                mic_kwargs["device_index"] = self.microphone_index

            self.microphone = sr.Microphone(**mic_kwargs)
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise (1s)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                logger.info(f"Ambient noise calibration complete (Energy Threshold: {self.recognizer.energy_threshold:.1f})")

            self.is_listening = True
            self._listen_thread = threading.Thread(target=self._worker_loop, daemon=True, name="LinnySTTWorker")
            self._listen_thread.start()
            self._event_bus.publish(EventType.STATE_CHANGED, {"state": "listening", "description": "Ready"})
            logger.info("SpeechListener background loop started")
            return True

        except Exception as e:
            logger.error(f"Failed to start microphone listener: {e}", exc_info=True)
            self.is_listening = False
            self._event_bus.publish(EventType.STATE_CHANGED, {"state": "error", "description": f"Mic Error: {e}"})
            return False

    def stop(self) -> None:
        """Stop speech listener."""
        self.is_listening = False
        self._stop_event.set()
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.0)
        logger.info("SpeechListener stopped")

    def _worker_loop(self) -> None:
        """Main listening loop with audio isolation."""
        while self.is_listening and not self._stop_event.is_set():
            if self.is_muted:
                time.sleep(0.15)
                continue

            try:
                with self.microphone as source:
                    # Listen for audio phrase
                    try:
                        audio = self.recognizer.listen(source, timeout=3.0, phrase_time_limit=8.0)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        logger.debug(f"Audio capture warning: {e}")
                        time.sleep(0.2)
                        continue

                # If muted or canceled while recording, discard
                if self.is_muted or not self.is_listening:
                    continue

                # Recognize speech via Google STT engine
                try:
                    self._event_bus.publish(EventType.STATE_CHANGED, {"state": "processing", "description": "Recognizing..."})
                    text = self.recognizer.recognize_google(audio)
                    if text and text.strip():
                        logger.info(f"Recognized Speech: '{text}'")
                        self._event_bus.publish(EventType.COMMAND_DETECTED, {"query": text, "source": "mic"})
                        # Dispatch command in non-blocking thread
                        dispatch_thread = threading.Thread(
                            target=self.on_command_callback,
                            args=(text,),
                            daemon=True,
                            name="LinnyCommandDispatcher",
                        )
                        dispatch_thread.start()
                except sr.UnknownValueError:
                    # Speech was unintelligible / background noise
                    pass
                except sr.RequestError as e:
                    logger.warning(f"Google Speech Recognition service unreachable: {e}")
                    time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"Speech recognition processing error: {e}")

            except Exception as e:
                logger.error(f"Unexpected error in STT loop: {e}", exc_info=True)
                time.sleep(0.5)
