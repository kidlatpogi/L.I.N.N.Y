"""
L.I.N.N.Y. v8.0 - Loyal Intelligent Neural Network for You
Complete Rewrite: Strict Class Separation, Hardcoded-First, Non-Blocking
"""

import os
import sys
import json
import threading
import asyncio
import tempfile
import logging
import subprocess
import webbrowser
import gc
import shutil
import time
import requests
import concurrent.futures
import re
from datetime import datetime, timedelta
from pathlib import Path
import ctypes

# GUI & System
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
import psutil

# Voice & Audio
import speech_recognition as sr
import edge_tts
import pygame
import pyautogui

# AI Providers
import groq
import google.generativeai as genai
from openai import OpenAI

# Google Calendar
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Utilities
import pytz
from dateutil import parser as date_parser
import pywhatkit

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LINNY")

# ============================================================================
# CONSTANTS
# ============================================================================
CONFIG_FILE = Path.home() / ".linny" / "linny_config.json"
TOKEN_FILE = Path.home() / ".linny" / "token.json"
CREDENTIALS_FILE = Path("credentials.json")
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# ============================================================================
# BRAIN MANAGER - Cascading AI
# ============================================================================
class BrainManager:
    """Cascading AI with Groq -> Gemini -> Perplexity fallback"""
    
    def __init__(self, config):
        self.config = config
        self.groq_client = None
        self.gemini_model = None
        self.perplexity_client = None
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all AI providers"""
        if self.config.get("groq_api_key"):
            try:
                self.groq_client = groq.Groq(api_key=self.config["groq_api_key"])
                logger.info("✓ Groq initialized")
            except Exception as e:
                logger.warning(f"Groq failed: {e}")
        
        if self.config.get("gemini_api_key"):
            try:
                genai.configure(api_key=self.config["gemini_api_key"])
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✓ Gemini initialized")
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        if self.config.get("perplexity_api_key"):
            try:
                self.perplexity_client = OpenAI(
                    api_key=self.config["perplexity_api_key"],
                    base_url="https://api.perplexity.ai"
                )
                logger.info("✓ Perplexity initialized")
            except Exception as e:
                logger.warning(f"Perplexity failed: {e}")
    
    def _is_search(self, query):
        """Detect search intent"""
        keywords = ["search", "price", "news", "weather", "latest", "who"]
        return any(k in query.lower() for k in keywords)
    
    def ask(self, query, user_name="User", language="English"):
        """Cascading ask: Perplexity (search) -> Groq -> Gemini -> Perplexity"""
        system = f"You are Linny, a helpful AI. User: {user_name}. Language: {language}. Be concise."
        
        is_search = self._is_search(query)
        
        # Search intent -> Try Perplexity first
        if is_search and self.perplexity_client:
            try:
                response = self.perplexity_client.chat.completions.create(
                    model="llama-3.1-sonar-small-128k-online",
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": query}]
                )
                logger.info("✓ Perplexity (search) responded")
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Perplexity failed: {e}")
        
        # Try Groq
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": query}],
                    temperature=0.7, max_tokens=500
                )
                logger.info("✓ Groq responded")
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq failed: {e}")
        
        # Try Gemini
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(f"{system}\n\nUser: {query}")
                logger.info("✓ Gemini responded")
                return response.text
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Perplexity fallback
        if not is_search and self.perplexity_client:
            try:
                response = self.perplexity_client.chat.completions.create(
                    model="llama-3.1-sonar-small-128k-online",
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": query}]
                )
                logger.info("✓ Perplexity (fallback) responded")
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Perplexity failed: {e}")
        
        return "All AI systems are offline. Please check your API keys."

# ============================================================================
# CALENDAR MANAGER
# ============================================================================
class CalendarManager:
    """Google Calendar with smart schedule filtering"""
    
    def __init__(self, timezone="Asia/Manila"):
        self.service = None
        self.timezone = pytz.timezone(timezone)
        self.school_cal_id = None
        self._auth()
    
    def _auth(self):
        """Authenticate with Google Calendar"""
        creds = None
        
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), CALENDAR_SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif CREDENTIALS_FILE.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), CALENDAR_SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                logger.warning("credentials.json not found. Calendar disabled.")
                return
            
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        logger.info("✓ Google Calendar authenticated")
        self._find_school_cal()
    
    def _find_school_cal(self):
        """Find School calendar"""
        if not self.service:
            return
        try:
            cals = self.service.calendarList().list().execute()
            for cal in cals.get('items', []):
                if cal.get('summary', '').lower() == 'school':
                    self.school_cal_id = cal['id']
                    logger.info(f"✓ School calendar: {self.school_cal_id}")
                    return
        except Exception as e:
            logger.warning(f"Could not find School calendar: {e}")
    
    def get_schedule(self):
        """Get today's schedule with smart filtering"""
        if not self.service:
            return "Calendar not configured."
        
        try:
            now = datetime.now(self.timezone)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            cal_id = self.school_cal_id or 'primary'
            
            events_result = self.service.events().list(
                calendarId=cal_id,
                timeMin=today_start.isoformat(),
                timeMax=today_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            ongoing = []
            upcoming = []
            
            for event in events:
                start_str = event['start'].get('dateTime', event['start'].get('date'))
                end_str = event['end'].get('dateTime', event['end'].get('date'))
                
                start_t = date_parser.parse(start_str)
                end_t = date_parser.parse(end_str)
                
                if start_t.tzinfo is None:
                    start_t = self.timezone.localize(start_t)
                if end_t.tzinfo is None:
                    end_t = self.timezone.localize(end_t)
                
                if end_t < now:
                    continue
                elif start_t < now < end_t:
                    ongoing.append((event, start_t, end_t))
                else:
                    upcoming.append((event, start_t, end_t))
            
            active = ongoing + upcoming
            
            if not active:
                return "You have no more schedule for today."
            
            summary = f"You have {len(active)} event(s) remaining:\n"
            for event, start_t, end_t in active[:5]:
                name = event.get('summary', 'Untitled')
                if start_t < now < end_t:
                    summary += f"- {name} (Ongoing, ends {end_t.strftime('%I:%M %p')})\n"
                else:
                    summary += f"- {name} ({start_t.strftime('%I:%M %p')} to {end_t.strftime('%I:%M %p')})\n"
            
            return summary.strip()
        except Exception as e:
            logger.error(f"Calendar error: {e}")
            return "Could not access calendar."

# ============================================================================
# VOICE ENGINE - TTS Only
# ============================================================================
class VoiceEngine:
    """Handles TTS with Edge TTS + Pygame playback. Manages is_speaking flag."""
    
    def __init__(self, voice="en-PH-RosaNeural"):
        self.voice = voice
        pygame.mixer.init()
        self.is_speaking = False
    
    def speak(self, text, callback=None):
        """Speak text asynchronously - is_speaking flag MUST be True before TTS"""
        def _thread():
            try:
                self.is_speaking = True
                logger.debug("🔒 TTS locked")
                
                # Generate TTS
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_path = temp_file.name
                temp_file.close()
                
                asyncio.run(edge_tts.Communicate(text, self.voice).save(temp_path))
                
                # Play
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                logger.debug("▶️ Playback started")
                
                # Wait until done
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.music.unload()
                os.unlink(temp_path)
                logger.debug("⏹️ Playback finished")
                
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                self.is_speaking = False
                logger.debug("🔓 TTS unlocked")
                if callback:
                    callback()
        
        threading.Thread(target=_thread, daemon=True).start()
    
    def set_voice(self, voice):
        """Change voice"""
        self.voice = voice

# ============================================================================
# SYSTEM TRAY MANAGER
# ============================================================================
class TrayManager:
    """System tray icon with state colors"""
    
    def __init__(self, on_show, on_mute, on_exit):
        self.icon = None
        self.on_show = on_show
        self.on_mute = on_mute
        self.on_exit = on_exit
        self.state = "listening"
    
    def _img(self, color):
        """Create colored circle"""
        img = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=color)
        return img
    
    def _menu(self):
        """Create tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Show Dashboard", self.on_show),
            pystray.MenuItem("Toggle Mute", self.on_mute),
            pystray.MenuItem("Exit", self.on_exit)
        )
    
    def start(self):
        """Start tray"""
        img = self._img('green')
        self.icon = pystray.Icon("LINNY", img, "L.I.N.N.Y. v8.0", self._menu())
        threading.Thread(target=self.icon.run, daemon=True).start()
        logger.info("✓ Tray started")
    
    def update_state(self, state):
        """Update icon color"""
        self.state = state
        if self.icon:
            colors = {"listening": "green", "speaking": "blue", "muted": "red"}
            self.icon.icon = self._img(colors.get(state, "gray"))
    
    def stop(self):
        """Stop tray"""
        if self.icon:
            self.icon.stop()

# ============================================================================
# LINNY ASSISTANT - Logic + Listening (Core Brain)
# ============================================================================
class LinnyAssistant:
    """Handles listening, command processing, and logic"""
    
    def __init__(self, config, voice, calendar, brain):
        self.config = config
        self.voice = voice
        self.calendar = calendar
        self.brain = brain
        
        self.is_listening = False
        self.is_muted = False
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._audio_source = None
        
        # Command executor for non-blocking execution
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    
    def _get_weather(self):
        """Fetch weather from Open-Meteo"""
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=14.32&longitude=120.93&current_weather=true&timezone=Asia%2FManila"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            cw = data.get('current_weather') or {}
            temp = cw.get('temperature')
            code = cw.get('weathercode')
            
            if temp is None:
                return "I couldn't read the temperature."
            
            condition = 'unknown'
            if code == 0:
                condition = 'clear'
            elif code in (1, 2, 3):
                condition = 'cloudy'
            elif 45 <= code <= 48:
                condition = 'foggy'
            elif 50 <= code <= 67 or 80 <= code <= 86:
                condition = 'rainy'
            elif code >= 95:
                condition = 'thunderstorms'
            else:
                condition = 'cloudy'
            
            return f"It is {round(temp)} degrees and {condition}."
        except Exception as e:
            logger.warning(f"Weather failed: {e}")
            return "Could not get weather."
    
    def _start_timer(self, text):
        """Start background timer"""
        try:
            match = re.search(r'(\d+)', text)
            if match:
                minutes = int(match.group(1))
                def timer():
                    time.sleep(minutes * 60)
                    self.voice.speak(f"Your {minutes} minute timer is done!")
                
                threading.Thread(target=timer, daemon=True).start()
                self.voice.speak(f"Timer set for {minutes} minutes.")
            else:
                self.voice.speak("I couldn't understand the duration.")
        except Exception as e:
            logger.error(f"Timer failed: {e}")
            self.voice.speak("Timer failed.")
    
    def execute_command(self, text):
        """
        HARDCODED-FIRST COMMAND EXECUTION
        Priority: System > Media > Apps > Time > Calendar > Weather > Clip > AI Brain
        """
        text_lower = text.lower()
        
        # Wake word check
        wake_words = ["linny", "lenny", "lini", "mini", "lhinny"]
        if not any(w in text_lower for w in wake_words):
            logger.debug(f"No wake word in: {text}")
            return
        
        logger.info(f"💬 Command: {text}")
        
        # ====================================================================
        # PRIORITY 1: SYSTEM COMMANDS
        # ====================================================================
        
        if any(w in text_lower for w in ["shutdown", "shut down"]):
            logger.info("⚡ System: Shutdown")
            self.voice.speak("Shutting down the system.")
            threading.Timer(3.0, lambda: os.system("shutdown /s /t 0")).start()
            return
        
        if "lock" in text_lower and any(w in text_lower for w in ["computer", "pc"]):
            logger.info("🔒 System: Lock")
            self.voice.speak("Locking workstation.")
            threading.Timer(1.0, lambda: ctypes.windll.user32.LockWorkStation()).start()
            return
        
        # ====================================================================
        # PRIORITY 2: MEDIA CONTROLS
        # ====================================================================
        
        if any(w in text_lower for w in ["resume", "unpause", "continue", "play music"]):
            logger.info("⏯️ Media: Play")
            pyautogui.press("playpause")
            self.voice.speak("Playing.")
            return
        
        if any(w in text_lower for w in ["pause", "stop music"]):
            logger.info("⏸️ Media: Pause")
            pyautogui.press("playpause")
            self.voice.speak("Paused.")
            return
        
        if any(w in text_lower for w in ["next", "skip"]):
            logger.info("⏭️ Media: Next")
            pyautogui.press("nexttrack")
            self.voice.speak("Next.")
            return
        
        if any(w in text_lower for w in ["volume up", "louder"]):
            logger.info("🔊 Media: Volume Up")
            for _ in range(2):
                pyautogui.press("volumeup")
            self.voice.speak("Volume up.")
            return
        
        if any(w in text_lower for w in ["volume down", "softer"]):
            logger.info("🔉 Media: Volume Down")
            for _ in range(2):
                pyautogui.press("volumedown")
            self.voice.speak("Volume down.")
            return
        
        if "mute" in text_lower and "unmute" not in text_lower:
            logger.info("🔇 Media: Mute")
            pyautogui.press("volumemute")
            self.voice.speak("Muted.")
            return
        
        # ====================================================================
        # PRIORITY 3: APP LAUNCHER
        # ====================================================================
        
        app_name = None
        for verb in ["open", "launch", "start"]:
            if verb in text_lower:
                parts = text_lower.split(verb, 1)
                if len(parts) > 1:
                    app_name = parts[1].strip()
                    break
        
        if app_name:
            for wake_word in wake_words:
                app_name = app_name.replace(wake_word, "").strip()
            
            logger.info(f"🚀 App: {app_name}")
            app_aliases = self.config.get("app_aliases", {})
            target = app_aliases.get(app_name, app_name)
            
            try:
                subprocess.Popen(
                    target,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=True
                )
                self.voice.speak(f"Opening {app_name}.")
            except Exception as e:
                logger.error(f"Failed to launch {app_name}: {e}")
                self.voice.speak(f"Couldn't find {app_name}.")
            return
        
        # ====================================================================
        # PRIORITY 4: TIME
        # ====================================================================
        
        if any(w in text_lower for w in ["time", "oras"]):
            logger.info("🕐 Time")
            tz = pytz.timezone(self.config.get("timezone", "Asia/Manila"))
            time_str = datetime.now(tz).strftime("%I:%M %p")
            self.voice.speak(f"It is {time_str}.")
            return
        
        # ====================================================================
        # PRIORITY 5: CALENDAR
        # ====================================================================
        
        if any(w in text_lower for w in ["schedule", "calendar", "agenda"]):
            logger.info("📅 Schedule")
            schedule = self.calendar.get_schedule()
            self.voice.speak(schedule)
            return
        
        # ====================================================================
        # PRIORITY 6: WEATHER
        # ====================================================================
        
        if any(w in text_lower for w in ["weather", "panahon"]):
            logger.info("🌤️ Weather")
            weather = self._get_weather()
            self.voice.speak(weather)
            return
        
        # ====================================================================
        # PRIORITY 7: TIMER
        # ====================================================================
        
        if "timer" in text_lower:
            logger.info("⏱️ Timer")
            self._start_timer(text_lower)
            return
        
        # ====================================================================
        # PRIORITY 8: CLIP
        # ====================================================================
        
        if any(w in text_lower for w in ["clip that", "record that"]):
            logger.info("📸 Clip")
            pyautogui.hotkey('alt', 'f10')
            self.voice.speak("Clipped.")
            return
        
        # ====================================================================
        # PRIORITY 9: PLAY ON YOUTUBE
        # ====================================================================
        
        if "play" in text_lower and "youtube" in text_lower:
            song = text_lower.replace("play", "").replace("on youtube", "").strip()
            for w in wake_words:
                song = song.replace(w, "").strip()
            
            if song and len(song) > 2:
                logger.info(f"🎵 YouTube: {song}")
                try:
                    pywhatkit.playonyt(song)
                    self.voice.speak(f"Playing {song}.")
                except Exception as e:
                    logger.error(f"YouTube failed: {e}")
                    self.voice.speak("YouTube failed.")
                return
        
        # ====================================================================
        # PRIORITY 10: AI BRAIN (FALLBACK)
        # ====================================================================
        
        logger.info("🤖 AI Brain")
        response = self.brain.ask(
            text,
            user_name=self.config.get("user_name", "User"),
            language=self.config.get("language", "English")
        )
        self.voice.speak(response)
    
    def _listen_loop(self):
        """IMMORTAL Non-Blocking Listening Loop"""
        logger.info("🎤 Listening loop started...")
        source = self._audio_source
        cycle = 0
        
        while self.is_listening:
            try:
                # STRICT AUDIO LOCKING: Don't listen while speaking
                while self.voice.is_speaking or self.is_muted:
                    logger.debug(f"🔒 Locked (speaking={self.voice.is_speaking}, muted={self.is_muted})")
                    time.sleep(0.1)
                
                cycle += 1
                if cycle % 100 == 0:
                    gc.collect()
                    logger.debug(f"🧹 Cycle {cycle}")
                
                if source is None:
                    logger.warning("Audio source lost, re-opening...")
                    try:
                        source = self.microphone.__enter__()
                        self._audio_source = source
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    except Exception as e:
                        logger.error(f"Re-open failed: {e}")
                        time.sleep(1)
                        continue
                
                try:
                    logger.debug("⏺️ Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    
                except sr.WaitTimeoutError:
                    logger.debug("⏳ Timeout")
                    continue
                except sr.UnknownValueError:
                    logger.debug("🔇 Unclear")
                    continue
                except sr.RequestError as e:
                    logger.warning(f"Recognition error: {e}")
                    continue
                except Exception as e:
                    logger.exception(f"Audio error: {e}")
                    time.sleep(0.5)
                    continue
                
                # Recognize
                try:
                    logger.debug("🔄 Recognizing...")
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"✨ Recognized: {text}")
                    
                    # FIRE-AND-FORGET: Spawn thread, loop continues immediately
                    threading.Thread(target=self.execute_command, args=(text,), daemon=True).start()
                    
                except sr.UnknownValueError:
                    logger.debug("🔇 No speech")
                    continue
                except sr.RequestError as e:
                    logger.warning(f"API error: {e}")
                    time.sleep(1)
                    continue
                except Exception as e:
                    logger.exception(f"Recognition error: {e}")
                    continue
                    
            except Exception as e:
                # CRITICAL: Never break the immortal loop
                logger.exception(f"[LOOP ERROR] {e}")
                try:
                    self.voice.speak("I encountered a glitch, but I'm back online.")
                except Exception:
                    pass
                time.sleep(0.5)
                continue
    
    def start_listening(self):
        """Start listening"""
        if not self.is_listening:
            try:
                self._audio_source = self.microphone.__enter__()
                logger.info("✓ Audio source opened")
                
                self.recognizer.adjust_for_ambient_noise(self._audio_source, duration=1)
                self.recognizer.pause_threshold = 0.8
                self.recognizer.dynamic_energy_threshold = False
                logger.info("✓ Recognizer configured")
            except Exception as e:
                logger.warning(f"Audio setup warning: {e}")
            
            self.is_listening = True
            threading.Thread(target=self._listen_loop, daemon=True).start()
            logger.info("✓ Listening thread started")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        if self._audio_source:
            try:
                self.microphone.__exit__(None, None, None)
            except Exception as e:
                logger.warning(f"Close audio failed: {e}")
    
    def toggle_mute(self):
        """Toggle mute"""
        self.is_muted = not self.is_muted
        state = "muted" if self.is_muted else "unmuted"
        logger.info(f"🔇 {state}")
        return self.is_muted

# ============================================================================
# LINNY APP - GUI + Tray (UI Layer Only)
# ============================================================================
class LinnyApp:
    """GUI and System Tray - Delegates all logic to LinnyAssistant"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.config = self._load_config()
        
        # Initialize components
        self.voice = VoiceEngine(self.config.get("voice_en", "en-PH-RosaNeural"))
        self.calendar = CalendarManager(self.config.get("timezone", "Asia/Manila"))
        self.brain = BrainManager(self.config)
        
        # CORE: LinnyAssistant handles all logic
        self.assistant = LinnyAssistant(self.config, self.voice, self.calendar, self.brain)
        
        # GUI
        if not headless:
            self._setup_gui()
        
        # Tray
        self.tray = TrayManager(
            on_show=self._show_dashboard,
            on_mute=self._toggle_mute,
            on_exit=self._exit_app
        )
        self.tray.start()
        
        # High priority
        try:
            psutil.Process(os.getpid()).nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("✓ High priority set")
        except Exception as e:
            logger.warning(f"Priority failed: {e}")
    
    def _load_config(self):
        """Load config"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Config JSON error: {e}")
                sys.exit(1)
        else:
            logger.error(f"Config not found: {CONFIG_FILE}")
            sys.exit(1)
    
    def _save_config(self):
        """Save config"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _setup_gui(self):
        """Setup GUI"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("L.I.N.N.Y. v8.0 - Dashboard")
        self.root.geometry("800x650")
        
        # Header
        header = ctk.CTkLabel(self.root, text="L.I.N.N.Y. v8.0", font=("Arial", 24, "bold"))
        header.pack(pady=20)
        
        # Status
        self.status_label = ctk.CTkLabel(self.root, text="Status: Ready", font=("Arial", 14))
        self.status_label.pack(pady=10)
        
        # Settings Frame
        settings_frame = ctk.CTkScrollableFrame(self.root, height=400)
        settings_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(settings_frame, text="Settings", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # User Name
        ctk.CTkLabel(settings_frame, text="Your Name:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.name_entry = ctk.CTkEntry(settings_frame, width=300)
        self.name_entry.insert(0, self.config.get("user_name", ""))
        self.name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Language
        ctk.CTkLabel(settings_frame, text="Language:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.lang_var = ctk.StringVar(value=self.config.get("language", "English"))
        lang_menu = ctk.CTkOptionMenu(settings_frame, variable=self.lang_var, values=["English", "Tagalog"], width=300)
        lang_menu.grid(row=2, column=1, padx=10, pady=5)
        
        # API Keys
        ctk.CTkLabel(settings_frame, text="Groq API Key:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.groq_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.groq_entry.insert(0, self.config.get("groq_api_key", ""))
        self.groq_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Gemini API Key:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.gemini_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.gemini_entry.insert(0, self.config.get("gemini_api_key", ""))
        self.gemini_entry.grid(row=4, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Perplexity API Key:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.perplexity_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.perplexity_entry.insert(0, self.config.get("perplexity_api_key", ""))
        self.perplexity_entry.grid(row=5, column=1, padx=10, pady=5)
        
        # Save Button
        save_btn = ctk.CTkButton(settings_frame, text="Save Settings", command=self._save_settings)
        save_btn.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Edit Aliases Button
        edit_btn = ctk.CTkButton(settings_frame, text="Edit App Aliases", command=self._edit_aliases)
        edit_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Control Frame
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=10)
        
        self.mute_btn = ctk.CTkButton(control_frame, text="Mute", command=self._toggle_mute, width=150)
        self.mute_btn.pack(side="left", padx=10)
        
        start_btn = ctk.CTkButton(control_frame, text="Start Listening", command=self._start_listening, width=150)
        start_btn.pack(side="left", padx=10)
        
        # Protocol
        self.root.protocol("WM_DELETE_WINDOW", self._hide_dashboard)
    
    def _save_settings(self):
        """Save settings"""
        self.config["user_name"] = self.name_entry.get()
        self.config["language"] = self.lang_var.get()
        self.config["groq_api_key"] = self.groq_entry.get()
        self.config["gemini_api_key"] = self.gemini_entry.get()
        self.config["perplexity_api_key"] = self.perplexity_entry.get()
        
        self._save_config()
        
        # Reinit
        self.brain = BrainManager(self.config)
        self.assistant.brain = self.brain
        
        logger.info("✓ Settings saved")
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Status: Settings Saved!")
    
    def _edit_aliases(self):
        """Edit config in Notepad"""
        try:
            if not CONFIG_FILE.exists():
                self._save_config()
            subprocess.Popen(['notepad.exe', str(CONFIG_FILE)])
            logger.info("✓ Config editor opened")
        except Exception as e:
            logger.error(f"Failed to open editor: {e}")
    
    def _show_dashboard(self):
        """Show GUI"""
        if hasattr(self, 'root'):
            self.root.deiconify()
    
    def _hide_dashboard(self):
        """Hide GUI"""
        if hasattr(self, 'root'):
            self.root.withdraw()
    
    def _toggle_mute(self):
        """Toggle mute"""
        is_muted = self.assistant.toggle_mute()
        self.tray.update_state("muted" if is_muted else "listening")
        if hasattr(self, 'mute_btn'):
            self.mute_btn.configure(text="Unmute" if is_muted else "Mute")
    
    def _start_listening(self):
        """Start listening"""
        self.assistant.start_listening()
        self.tray.update_state("listening")
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Status: Listening...")
    
    def _exit_app(self):
        """Exit"""
        logger.info("Exiting...")
        self.assistant.stop_listening()
        self.tray.stop()
        if hasattr(self, 'root'):
            self.root.quit()
        sys.exit(0)
    
    def run(self):
        """Run app"""
        if self.headless:
            try:
                while True:
                    pygame.time.Clock().tick(1)
            except KeyboardInterrupt:
                self._exit_app()
        else:
            self.root.mainloop()

# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    """Main entry"""
    headless = "--startup" in sys.argv
    app = LinnyApp(headless=headless)
    if not headless:
        app._start_listening()
    app.run()

if __name__ == "__main__":
    main()
