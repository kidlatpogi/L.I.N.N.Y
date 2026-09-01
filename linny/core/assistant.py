"""
Core Linny Voice Assistant Engine and Intent Router.
Dispatches voice and text queries to system actions, media controls,
smart home automation, Google Calendar, weather, app launcher, and AI brain.
"""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime
from typing import Callable, List, Optional

import pytz

from ..audio.stt import SpeechListener
from ..audio.tts import VoiceEngine
from ..integrations.ai_brain import AIBrain
from ..integrations.calendar import CalendarClient
from ..integrations.smart_home import SmartDeviceManager
from ..integrations.weather import WeatherClient
from ..system.launcher import AppLauncher
from ..system.power import SystemPowerManager
from ..system.startup import StartupManager
from .config import LinnyConfig, save_config
from .events import EventBus, EventType
from .logger import get_logger

logger = get_logger("assistant")

WAKE_WORDS = [
    "linny", "lenny", "lini", "leni", "linnie", "lynny", "lanny",
    "hey linny", "ok linny", "okay linny", "hi linny", "hello linny",
    "mini", "minny", "minnie", "mimi", "dini", "dinny", "nini", "ninny",
    "ginny", "hinny", "finny", "vinny", "winny", "pinny", "lhinny",
]


class LinnyAssistant:
    """Master orchestrator connecting audio streams, system services, and AI reasoning."""

    def __init__(self, config: LinnyConfig) -> None:
        self.config = config
        self.event_bus = EventBus()

        # Initialize sub-engines
        self.voice = VoiceEngine(
            voice_name=self.config.voice_en,
            rate=self.config.tts_rate,
            volume=self.config.tts_volume,
            preferred_engine=self.config.tts_engine,
        )
        self.brain = AIBrain(self.config)
        self.smart_home = SmartDeviceManager(self.config)
        self.calendar = CalendarClient(self.config.timezone)
        self.weather = WeatherClient(
            latitude=self.config.weather_latitude,
            longitude=self.config.weather_longitude,
            timezone=self.config.timezone,
            city_name=self.config.weather_city,
        )
        self.launcher = AppLauncher(self.config.app_aliases)
        self.power = SystemPowerManager(self.config.screenshot_folder)

        # Initialize STT Listener
        self.listener = SpeechListener(
            on_command_callback=self.handle_voice_query,
            microphone_index=self.config.microphone_index,
        )

        logger.info("LinnyAssistant successfully initialized")

    def reload_config(self, new_config: LinnyConfig) -> None:
        """Apply updated configuration across all subsystems."""
        self.config = new_config
        self.voice.set_voice(new_config.voice_en)
        self.voice.set_volume(new_config.tts_volume)
        self.voice.preferred_engine = new_config.tts_engine
        self.brain.reload(new_config)
        self.smart_home.reload(new_config)
        self.calendar.reload_timezone(new_config.timezone)
        self.weather.update_coordinates(
            new_config.weather_latitude,
            new_config.weather_longitude,
            new_config.timezone,
            city=new_config.weather_city,
        )
        self.launcher.update_aliases(new_config.app_aliases)
        self.power.screenshot_dir = new_config.screenshot_folder
        self.event_bus.publish(EventType.SETTINGS_SAVED, {"config": new_config.to_dict()})
        logger.info("Assistant configuration reloaded")

    def start(self) -> bool:
        """Start listening and elevate process priority."""
        StartupManager.set_high_priority()
        return self.listener.start()

    def stop(self) -> None:
        """Stop listening and speech synthesis."""
        self.voice.stop()
        self.listener.stop()

    def toggle_mute(self) -> bool:
        return self.listener.toggle_mute()

    def is_wake_word_present(self, text: str) -> Tuple[bool, str]:
        """Check if wake word is present and extract command text."""
        t_lower = text.lower().strip()
        for w in WAKE_WORDS:
            if w in t_lower:
                # Remove wake word from command string
                pattern = re.compile(re.escape(w), re.IGNORECASE)
                cleaned = pattern.sub("", text).strip()
                return True, cleaned
        return False, text

    def handle_voice_query(self, raw_text: str) -> None:
        """Entry point for incoming voice transcriptions."""
        if not raw_text or not raw_text.strip():
            return

        has_wake, clean_command = self.is_wake_word_present(raw_text)
        if not has_wake:
            logger.debug(f"Ignored speech without wake word: '{raw_text}'")
            return

        logger.info(f"Processing command: '{clean_command or raw_text}'")
        self.execute_command(clean_command or raw_text)

    def execute_command(self, query: str) -> None:
        """
        Intent routing with strict priority evaluation:
        1. System Power & Workstation
        2. Media playback controls
        3. Smart bulb & lighting presets
        4. Application & Website Launching
        5. Time & Date queries
        6. Calendar Agenda
        7. Weather Forecast
        8. Timers
        9. Screenshot & Video Clipping
        10. YouTube Streaming
        11. Assistant Control (Mute/Sleep)
        12. AI Brain Reasoning (Fallback)
        """
        q_lower = query.lower().strip()

        # Helper: Speak with temporary listener mute to prevent echo
        def _speak(msg: str) -> None:
            self.listener.set_muted(True)

            def _unmute():
                time.sleep(0.5)
                self.listener.set_muted(False)

            self.voice.speak(msg, callback=_unmute)

        # --------------------------------------------------------------------
        # Priority 1: System Power & Lock
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["shutdown", "shut down", "turn off pc"]):
            logger.info("Command: Shutdown PC")
            self.smart_home.turn_off()
            _speak("Shutting down the system. Goodbye!")
            self.power.shutdown(delay_seconds=3)
            return

        if any(w in q_lower for w in ["restart pc", "reboot pc", "restart system"]):
            logger.info("Command: Restart PC")
            _speak("Restarting the system.")
            self.power.restart(delay_seconds=3)
            return

        if "lock" in q_lower and any(w in q_lower for w in ["pc", "computer", "screen", "workstation"]):
            logger.info("Command: Lock Workstation")
            _speak("Locking your workstation.")
            threading.Timer(1.0, self.power.lock_workstation).start()
            return

        if "sleep" in q_lower and any(w in q_lower for w in ["pc", "computer", "system"]):
            logger.info("Command: Sleep PC")
            _speak("Putting the system to sleep.")
            self.power.sleep(delay_seconds=1)
            return

        # --------------------------------------------------------------------
        # Priority 2: Media Controls
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["resume", "unpause", "play music", "continue music"]):
            logger.info("Media: Play/Resume")
            self.power.media_play_pause()
            _speak("Resuming playback.")
            return

        if any(w in q_lower for w in ["pause", "stop music", "pause music"]):
            logger.info("Media: Pause")
            self.power.media_play_pause()
            _speak("Paused.")
            return

        if any(w in q_lower for w in ["next song", "next track", "skip song", "skip track"]):
            logger.info("Media: Next Track")
            self.power.media_next()
            _speak("Skipping track.")
            return

        if any(w in q_lower for w in ["previous song", "prev song", "previous track"]):
            logger.info("Media: Previous Track")
            self.power.media_prev()
            _speak("Previous track.")
            return

        if any(w in q_lower for w in ["volume up", "louder", "increase volume"]):
            logger.info("Media: Volume Up")
            self.power.media_volume_up()
            _speak("Volume increased.")
            return

        if any(w in q_lower for w in ["volume down", "softer", "decrease volume", "lower volume"]):
            logger.info("Media: Volume Down")
            self.power.media_volume_down()
            _speak("Volume lowered.")
            return

        if q_lower == "mute" or "mute audio" in q_lower:
            logger.info("Media: Mute Audio")
            self.power.media_mute()
            _speak("Audio muted.")
            return

        # --------------------------------------------------------------------
        # Priority 3: Smart Light Controls (Tapo & Kasa)
        # --------------------------------------------------------------------
        # Brightness percentage
        if ("light" in q_lower or "bulb" in q_lower or "brightness" in q_lower) and any(c in q_lower for c in ["%", "percent", "set", "to"]):
            match = re.search(r"(\d+)", q_lower)
            if match:
                level = int(match.group(1))
                if self.smart_home.set_brightness(level):
                    _speak(f"Lights set to {level} percent.")
                else:
                    _speak("Smart bulb is currently offline or unreachable.")
                return

        # Specific Color
        if "color" in q_lower and any(w in q_lower for w in ["light", "bulb", "lamp"]):
            for color_name in ["red", "crimson", "blue", "cyan", "green", "violet", "purple", "yellow", "orange", "pink", "warm"]:
                if color_name in q_lower:
                    if self.smart_home.set_color(color_name):
                        _speak(f"Lights set to {color_name}.")
                    else:
                        _speak(f"I couldn't change the light color to {color_name}.")
                    return

        # Light Modes
        if any(m in q_lower for m in ["focus mode", "movie mode", "gaming mode", "game mode", "night mode", "relax mode"]):
            for mode in ["focus", "movie", "gaming", "night", "relax"]:
                if mode in q_lower:
                    if self.smart_home.set_mode(mode):
                        _speak(f"{mode.capitalize()} mode activated.")
                    else:
                        _speak(f"Smart bulb is currently offline.")
                    return

        # Turn On Lights
        if any(w in q_lower for w in [
            "turn on lights", "lights on", "turn on the light", "turn on bulb", "bulb on",
            "buksan ilaw", "buksan ang ilaw", "buksan mo ang ilaw"
        ]):
            if self.smart_home.turn_on():
                _speak("Lights turned on.")
            else:
                _speak("I couldn't reach the smart bulb.")
            return

        # Turn Off Lights
        if any(w in q_lower for w in [
            "turn off lights", "lights off", "turn off the light", "turn off bulb", "bulb off",
            "patayin ilaw", "patayin ang ilaw", "patay ilaw"
        ]):
            if self.smart_home.turn_off():
                _speak("Lights turned off.")
            else:
                _speak("I couldn't reach the smart bulb.")
            return

        # --------------------------------------------------------------------
        # Priority 4: Application / Game / Website Launching
        # --------------------------------------------------------------------
        launch_verb = None
        for verb in ["launch", "open", "start", "run", "accio"]:
            if verb in q_lower:
                parts = q_lower.split(verb, 1)
                if len(parts) > 1 and parts[1].strip():
                    target_app = parts[1].strip()
                    # Clean wake words that might follow
                    for w in WAKE_WORDS:
                        target_app = target_app.replace(w, "").strip()
                    if target_app:
                        success, message = self.launcher.launch(target_app)
                        _speak(message)
                        return

        # --------------------------------------------------------------------
        # Priority 5: Time & Date
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["what time", "current time", "anong oras", "oras na", "time check"]):
            tz = pytz.timezone(self.config.timezone)
            now = datetime.now(tz)
            time_str = now.strftime("%I:%M %p")
            _speak(f"It is {time_str}.")
            return

        if any(w in q_lower for w in ["what date", "what is the date", "anong petsa", "what day is today", "today's date"]):
            tz = pytz.timezone(self.config.timezone)
            now = datetime.now(tz)
            date_str = now.strftime("%A, %B %d, %Y")
            _speak(f"Today is {date_str}.")
            return

        # --------------------------------------------------------------------
        # Priority 6: Google Calendar & Schedule
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["schedule", "calendar", "agenda", "events today", "what do i have today"]):
            summary = self.calendar.get_schedule(query=q_lower)
            _speak(summary)
            return

        # --------------------------------------------------------------------
        # Priority 7: Weather Forecast
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["weather", "panahon", "temperature", "is it going to rain", "forecast"]):
            weather_text = self.weather.get_voice_summary()
            _speak(weather_text)
            return

        # --------------------------------------------------------------------
        # Priority 8: Timers
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["timer", "set timer", "set a timer", "pomodoro"]):
            match = re.search(r"(\d+)", q_lower)
            if match:
                minutes = int(match.group(1))

                def _timer_job():
                    time.sleep(minutes * 60)
                    _speak(f"Attention {self.config.user_name}, your {minutes} minute timer is complete!")

                threading.Thread(target=_timer_job, daemon=True).start()
                _speak(f"Timer set for {minutes} minute{'s' if minutes > 1 else ''}.")
            else:
                _speak("I couldn't detect the timer duration.")
            return

        # --------------------------------------------------------------------
        # Priority 9: Screen Capture & Video Clip
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["clip that", "record that", "save clip"]):
            if self.power.trigger_clip():
                _speak("Replay clipped.")
            else:
                _speak("Could not trigger replay clip.")
            return

        if any(w in q_lower for w in ["take screenshot", "screenshot", "capture screen", "capture display"]):
            ok, path = self.power.take_screenshot()
            if ok:
                _speak("Fullscreen screenshot saved.")
            else:
                _speak("Failed to capture screenshot.")
            return

        # --------------------------------------------------------------------
        # Priority 10: YouTube Playback
        # --------------------------------------------------------------------
        if "play" in q_lower and "youtube" in q_lower:
            song = q_lower.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
            for w in WAKE_WORDS:
                song = song.replace(w, "").strip()
            if song and len(song) > 1:
                try:
                    import pywhatkit
                    pywhatkit.playonyt(song)
                    _speak(f"Playing {song} on YouTube.")
                except Exception as e:
                    logger.error(f"YouTube playback error: {e}")
                    _speak("Could not start YouTube playback.")
                return

        # --------------------------------------------------------------------
        # Priority 11: Assistant Mute / Stop Listening
        # --------------------------------------------------------------------
        if any(w in q_lower for w in ["stop listening", "go to sleep", "mute mic", "quiet linny"]):
            _speak("Going on standby. Tap unmute or press hotkey to resume.")
            self.listener.set_muted(True)
            return

        # --------------------------------------------------------------------
        # Priority 12: Cascading Multi-LLM AI Brain
        # --------------------------------------------------------------------
        logger.info(f"Routing to AI Brain: '{query}'")
        ai_response = self.brain.ask(query)
        _speak(ai_response)

    def run_startup_sequence(self) -> None:
        """
        Execute startup sequence:
        1. Lock workstation immediately if lock_on_startup is enabled.
        2. Set high process priority.
        3. Start listening thread.
        4. Synthesize asynchronous morning greeting with date, weather, and schedule.
        """
        logger.info("Executing Linny startup sequence...")

        if self.config.lock_on_startup:
            logger.info("Lock on startup enabled -> Locking workstation")
            self.power.lock_workstation()

        StartupManager.set_high_priority()
        self.start()

        def _greeting_worker():
            try:
                time.sleep(2.5)  # Allow audio output drivers to settle
                tz = pytz.timezone(self.config.timezone)
                now = datetime.now(tz)
                hour = now.hour

                if 5 <= hour < 12:
                    greeting = f"Good morning, {self.config.user_name}."
                elif 12 <= hour < 18:
                    greeting = f"Good afternoon, {self.config.user_name}."
                else:
                    greeting = f"Good evening, {self.config.user_name}."

                date_time_msg = f"It is {now.strftime('%A, %B %d')}, at {now.strftime('%I:%M %p')}."

                # Get weather
                try:
                    weather_summary = self.weather.get_voice_summary()
                except Exception:
                    weather_summary = ""

                # Get calendar schedule
                try:
                    schedule_summary = self.calendar.get_schedule("")
                except Exception:
                    schedule_summary = ""

                full_greeting = f"{greeting} {date_time_msg} {weather_summary} {schedule_summary}".strip()
                logger.info(f"Startup Greeting: {full_greeting}")
                self.voice.speak(full_greeting)

            except Exception as e:
                logger.error(f"Startup greeting error: {e}")

        threading.Thread(target=_greeting_worker, daemon=True, name="LinnyStartupGreeting").start()
