"""
L.I.N.N.Y. v9.4 - Loyal Intelligent Neural Network for You
"""

import os
import sys
import json
import threading
import logging
import subprocess
import webbrowser
import time
import requests
import re
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import ctypes
import gc

# GUI & System
# customtkinter and PIL imported lazily in _setup_gui()
import pystray
import psutil

# Voice & Audio
import speech_recognition as sr
import pyttsx3
import pyautogui
import keyboard  # Global hotkey support

# AI Providers
import groq
import google.generativeai as genai

# Google Calendar
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Smart Home
try:
    from kasa import Device, Discover
    from kasa import Credentials as TapoCredentials
    from kasa import DeviceConfig, Module
except ImportError:
    Device = None
    Discover = None
    TapoCredentials = None
    DeviceConfig = None
    Module = None

# Utilities
import pytz
from dateutil import parser as date_parser
import pywhatkit

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LINNY")

# Silence verbose libraries
logging.getLogger('googleapiclient').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
logging.getLogger('kasa').setLevel(logging.WARNING)
logging.getLogger('comtypes').setLevel(logging.WARNING)
logging.getLogger('comtypes._comobject').setLevel(logging.WARNING)
logging.getLogger('comtypes._vtbl').setLevel(logging.WARNING)
logging.getLogger('comtypes.client').setLevel(logging.WARNING)
logging.getLogger('comtypes._post_coinit').setLevel(logging.WARNING)

# ============================================================================
# CONSTANTS & DEFAULT CONFIG
# ============================================================================
CONFIG_FILE = Path.home() / ".linny" / "linny_config.json"
TOKEN_FILE = Path.home() / ".linny" / "token.json"
CREDENTIALS_FILE = Path("credentials.json")
DEFAULT_CONFIG_FILE = Path("linny_config_default.json")
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# ============================================================================
# LIGHT MANAGER - Tapo L530E Smart Bulb
# ============================================================================
class LightManager:
    """Control Tapo L530E smart bulb via kasa with authentication"""
    
    def __init__(self, config=None):
        """Initialize with config containing IP, email, and password"""
        if config is None:
            config = {}
        
        self.config = config
        self.ip = config.get("smart_bulb_ip", "<BULB_IP>")
        self.tapo_email = config.get("tapo_email", "")
        self.tapo_password = config.get("tapo_password", "")
        self.bulb = None
        self.loop = None  # Store event loop for reuse
        self._connect()
    
    def _ensure_connected(self):
        """Check if bulb is connected, return True if connected"""
        if not self.bulb or not self.loop:
            logger.warning("Smart bulb not available")
            return False
        return True
    
    def _get_light_module(self):
        """Get light module from bulb, returns None if not available"""
        if Module and Module.Light in self.bulb.modules:
            return self.bulb.modules[Module.Light]
        elif 'Light' in self.bulb.modules:
            return self.bulb.modules['Light']
        else:
            logger.error(f"Light module not found. Available: {list(self.bulb.modules.keys())}")
            return None
    
    def _log_auth_error(self):
        """Log authentication error message"""
        logger.error("❌ Tapo Authentication Failed. Please check your email and password in settings.")
    
    def _connect(self):
        """Connect to smart bulb with authentication"""
        if Device is None:
            logger.warning("kasa not installed, smart bulb disabled")
            return
        
        try:
            # Create and store event loop for reuse
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Import Discover for device discovery
            from kasa import Discover
            
            # Use discover_single for Tapo devices (handles port 20002)
            if self.tapo_email and self.tapo_password and TapoCredentials is not None:
                logger.info(f"🔐 Discovering Tapo bulb with authentication: {self.ip}")
                creds = TapoCredentials(username=self.tapo_email, password=self.tapo_password)
                self.bulb = self.loop.run_until_complete(Discover.discover_single(self.ip, credentials=creds))
                # Update device to load modules
                self.loop.run_until_complete(self.bulb.update())
                logger.info(f"✓ Smart bulb connected (authenticated): {self.ip}")

            else:
                # Fallback to discovery without credentials
                logger.info(f"🔌 Discovering bulb without authentication: {self.ip}")
                self.bulb = self.loop.run_until_complete(Discover.discover_single(self.ip))
                # Update device to load modules
                self.loop.run_until_complete(self.bulb.update())
                logger.info(f"✓ Smart bulb connected: {self.ip}")

        except Exception as e:
            logger.warning(f"Smart bulb connection failed: {e}")
            if "auth" in str(e).lower() or "credentials" in str(e).lower():
                self._log_auth_error()
            self.bulb = None
            self.loop = None
    
    def set_mode(self, mode):
        """Set bulb mode: Focus, Movie, Gaming"""
        if not self._ensure_connected():
            return
        
        try:
            # Debug: Show available modules
            logger.info(f"Available modules: {list(self.bulb.modules.keys())}")
            
            # Access light module for bulb control
            light = self._get_light_module()
            if not light:
                return
            
            # Reuse the same event loop from connection
            if mode.lower() == "focus":
                # 6000K, 100% brightness
                logger.info("💡 Setting Focus mode: 6000K, 100% brightness")
                self.loop.run_until_complete(light.set_brightness(100))
                self.loop.run_until_complete(light.set_color_temp(6000))
                logger.info("💡 Focus mode activated")

            elif mode.lower() == "movie":
                # 2500K, 30% brightness
                logger.info("🎬 Setting Movie mode: 2500K, 30% brightness")
                self.loop.run_until_complete(light.set_brightness(30))
                self.loop.run_until_complete(light.set_color_temp(2500))
                logger.info("🎬 Movie mode activated")

            elif mode.lower() == "gaming":
                # Purple HSV(280, 100, 60)
                logger.info("🎮 Setting Gaming mode: Purple HSV(280, 100, 60)")
                self.loop.run_until_complete(light.set_hsv(280, 100, 60))
                logger.info("🎮 Gaming mode activated")
                
            else:
                logger.warning(f"Unknown mode: {mode}")
            
        except AttributeError as e:
            logger.error(f"Light module method not available: {e}")
        except Exception as e:
            logger.error(f"Failed to set mode: {e}", exc_info=True)
            if "auth" in str(e).lower() or "credentials" in str(e).lower():
                self._log_auth_error()
    
    def turn_on(self):
        """Turn on bulb"""
        if not self._ensure_connected():
            return
        try:
            self.loop.run_until_complete(self.bulb.turn_on())
            logger.info("💡 Bulb turned on")
        except Exception as e:
            logger.error(f"Failed to turn on bulb: {e}")
            if "auth" in str(e).lower() or "credentials" in str(e).lower():
                self._log_auth_error()
    
    def turn_off(self):
        """Turn off bulb"""
        if not self._ensure_connected():
            return
        try:
            self.loop.run_until_complete(self.bulb.turn_off())
            logger.info("🔦 Bulb turned off")
        except Exception as e:
            logger.error(f"Failed to turn off bulb: {e}")
            if "auth" in str(e).lower() or "credentials" in str(e).lower():
                self._log_auth_error()

    def set_brightness(self, level):
        """Set specific brightness level (0-100)"""
        if not self._ensure_connected():
            return False
        
        try:
            # Get light module
            light = self._get_light_module()
            if not light:
                return False
            
            # Clamp level
            level = max(0, min(100, int(level)))
            
            logger.info(f"💡 Setting brightness to {level}%")
            self.loop.run_until_complete(light.set_brightness(level))
            return True
            
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False

    def set_color(self, color_name):
        """Set bulb color by name"""
        if not self._ensure_connected():
            return False
        
        try:
            # Get light module
            light = self._get_light_module()
            if not light:
                return False
            
            color_map = {
                "red": (0, 100, 100),
                "blue": (240, 100, 100),
                "violet": (270, 100, 100),
                "green": (120, 100, 100),
                "warm": None  # Special case for temp
            }
            
            target = color_name.lower()
            if target not in color_map:
                return False
            
            logger.info(f"🎨 Setting color to {target}")
            
            if target == "warm":
                # Warm White (2700K)
                self.loop.run_until_complete(light.set_color_temp(2700))
            else:
                # HSV Colors
                h, s, v = color_map[target]
                self.loop.run_until_complete(light.set_hsv(h, s, v))
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to set color: {e}")
            return False
            
class BrainManager:
    """Cascading AI: Groq -> Gemini -> Perplexity (via requests)"""
    
    def __init__(self, config):
        self.config = config
        self.groq_client = None
        self.gemini_model = None
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
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("✓ Gemini initialized")
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
    
    def _is_search(self, query):
        """Detect search intent"""
        keywords = ["search", "price", "news", "latest", "who", "what", "how"]
        return any(k in query.lower() for k in keywords)
    
    def _ask_perplexity(self, query, system):
        """Ask Perplexity via raw HTTP requests"""
        if not self.config.get("perplexity_api_key"):
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['perplexity_api_key']}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": query}
                ]
            }
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            logger.info("✓ Perplexity responded")
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.warning(f"Perplexity failed: {e}")
            return None
    
    def ask(self, query, user_name="User", language="English"):
        """Cascading ask: Search -> Perplexity, Chat -> Groq, Error -> Gemini"""
        system = f"You are Linny, a helpful AI assistant. User: {user_name}. Language: {language}. Be concise (1-2 sentences)."
        
        is_search = self._is_search(query)
        
        # Search/News queries -> Perplexity first
        if is_search:
            result = self._ask_perplexity(query, system)
            if result:
                return result
        
        # Regular chat -> Groq
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
        
        # Fallback to Gemini
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(f"{system}\n\nUser: {query}")
                logger.info("✓ Gemini responded")
                return response.text
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Last resort: Perplexity general query
        result = self._ask_perplexity(query, system)
        if result:
            return result
        
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
    
    def _ensure_timezone_aware(self, dt):
        """Ensure datetime is timezone-aware"""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt
    
    def get_schedule(self, query=""):
        """Get schedule with smart intent detection"""
        if not self.service:
            return "Calendar not configured."
        
        try:
            now = datetime.now(self.timezone)
            query_lower = query.lower() if query else ""
            is_tomorrow_request = any(w in query_lower for w in ["tomorrow", "bukas", "next day"])
            
            if is_tomorrow_request:
                logger.info("📅 Tomorrow schedule requested")
                target_day = now + timedelta(days=1)
                day_start = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                label = "tomorrow"
            else:
                logger.info("📅 Today/Smart schedule requested")
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                label = "today"
            
            cal_id = self.school_cal_id or 'primary'
            events_result = self.service.events().list(
                calendarId=cal_id,
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
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
                
                start_t = self._ensure_timezone_aware(start_t)
                end_t = self._ensure_timezone_aware(end_t)
                
                if label == "today" and end_t < now:
                    continue
                elif start_t < now < end_t:
                    ongoing.append((event, start_t, end_t))
                else:
                    upcoming.append((event, start_t, end_t))
            
            active = ongoing + upcoming
            
            # SMART SWITCH: If today is empty, try tomorrow
            if not active and label == "today" and not is_tomorrow_request:
                logger.info("📅 Today empty, switching to tomorrow")
                return self.get_schedule("tomorrow")
            
            if not active:
                return f"You have no schedule for {label}."
            
            day_name = "Tomorrow" if label == "tomorrow" else "Today"
            summary = f"{day_name}: {len(active)} event(s)\n"
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
    """Offline TTS Engine using pyttsx3 - Zero Latency, No Network Dependencies"""
    
    def __init__(self, voice=None):
        """
        Initialize pyttsx3 engine with optimal settings for Linny.
        
        Args:
            voice: Optional voice ID. If None, selects first female voice.
        """
        self.engine = pyttsx3.init()
        self.is_speaking = False
        self._interrupt = False
        
        # Get available voices
        available_voices = self.engine.getProperty('voices')
        
        # Select voice: prioritize female voices
        selected_voice = None
        if voice:
            # Use specified voice ID
            selected_voice = voice
        else:
            # Try to find female voice (usually Zira on Windows)
            for v in available_voices:
                if 'zira' in v.name.lower() or 'female' in v.name.lower():
                    selected_voice = v.id
                    break
            
            # Fallback: use second voice if available
            if not selected_voice and len(available_voices) > 1:
                selected_voice = available_voices[1].id
            elif not selected_voice:
                selected_voice = available_voices[0].id
        
        # Apply voice and settings
        if selected_voice:
            self.engine.setProperty('voice', selected_voice)
        self.engine.setProperty('rate', 150)      # Speech rate (words per minute)
        self.engine.setProperty('volume', 1.0)    # Volume (0.0 to 1.0)
    
    def stop(self):
        """Stop current speech immediately"""
        self._interrupt = True
        try:
            self.engine.stop()
        except Exception as e:
            logger.error(f"Error stopping TTS: {e}")
        finally:
            self.is_speaking = False
    
    def speak(self, text, callback=None):
        """
        Speak text asynchronously in a separate thread (non-blocking).
        
        Args:
            text: Text to speak
            callback: Optional function to call when speech finishes
        """
        def _thread():
            try:
                self._interrupt = False
                self.is_speaking = True
                
                # Speak synchronously (pyttsx3 blocks until done or stopped)
                self.engine.say(text)
                self.engine.runAndWait()
                
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                self.is_speaking = False
                if callback:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
        
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
        from PIL import Image, ImageDraw  # Lazy import
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
        self.icon = pystray.Icon("L.I.N.N.Y.", img, "L.I.N.N.Y. v9.4", self._menu())
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
# LINNY ASSISTANT - Core Logic + Listening
# ============================================================================
class LinnyAssistant:
    """Handles listening, command processing, and logic"""
    
    def __init__(self, config, voice, calendar, brain, lights, tray=None):
        self.config = config
        self.voice = voice
        self.calendar = calendar
        self.brain = brain
        self.lights = lights
        self.tray = tray
        
        self.is_listening = False
        self.is_muted = False
        
        self.recognizer = sr.Recognizer()
        # Allow user to configure specific microphone from config
        mic_index = self.config.get("microphone_index", None)
        self.microphone = sr.Microphone(device_index=mic_index) if mic_index is not None else sr.Microphone()
        self._audio_source = None
        
        # Log which microphone is being used
        if mic_index is not None:
            try:
                mics = sr.Microphone.list_microphone_names()
                logger.info(f"🎤 Using microphone: [{mic_index}] {mics[mic_index] if mic_index < len(mics) else 'Unknown'}")
            except:
                pass
    
    def _get_weather(self):
        """Fetch weather from Open-Meteo with contextual advice"""
        try:
            # Coordinates for Anahaw 2, Bulihan, Silang, Cavite, Philippines
            url = "https://api.open-meteo.com/v1/forecast?latitude=14.2167&longitude=120.9833&current_weather=true&timezone=Asia%2FManila"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            cw = data.get('current_weather') or {}
            temp = cw.get('temperature')
            code = cw.get('weathercode')
            
            if temp is None:
                return "I couldn't read the temperature."
            
            condition = 'unknown'
            advice = ''
            
            if code == 0:
                condition = 'clear'
                advice = 'Wear sunscreen.'
            elif code in (1, 2, 3):
                condition = 'cloudy'
                advice = 'It might rain later, consider bringing an umbrella.'
            elif 45 <= code <= 48:
                condition = 'foggy'
                advice = 'Drive carefully, visibility is low.'
            elif 50 <= code <= 67 or 80 <= code <= 86:
                condition = 'rainy'
                advice = 'Bring an umbrella.'
            elif code >= 95:
                condition = 'thunderstorms'
                advice = 'Stay indoors if possible.'
            else:
                condition = 'cloudy'
                advice = 'Have a great day.'
            
            return f"It is {round(temp)} degrees and {condition}. {advice}"
        except requests.exceptions.Timeout:
            logger.warning(f"Weather API timeout after 10 seconds")
            return "Weather service is slow."
        except requests.exceptions.RequestException as e:
            logger.warning(f"Weather API request failed: {e}")
            return "Could not get weather."
        except Exception as e:
            logger.error(f"Weather failed: {e}", exc_info=True)
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
    
    def _launch_app(self, app_name):
        """
        Smart App Launcher with 3-case logic:
        Case A: URL (http/www) → webbrowser.open()
        Case B: System App/Protocol (no args) → os.startfile()
        Case C: Complex Command (args/spaces) → subprocess.Popen(shell=True)
        
        Mutes mic immediately to prevent echo, unmutes 2s after TTS completes.
        """
        app_name_lower = app_name.lower()
        app_aliases = self.config.get("app_aliases", {})
        target = app_aliases.get(app_name_lower, app_name_lower)
        
        logger.info(f"🚀 Launching: {app_name}")
        
        # MUTE IMMEDIATELY to prevent echo detection
        self.is_muted = True
        time.sleep(0.15)  # Give listening loop time to detect mute flag
        
        def _post_launch_unmute():
            """Callback to unmute mic 2 seconds after TTS completes"""
            time.sleep(2)
            self.is_muted = False
        
        try:
            # ================================================================
            # CASE A: URL (starts with http or www)
            # ================================================================
            if target.startswith("http://") or target.startswith("https://") or target.startswith("www"):
                logger.info(f"📡 Case A: URL → {target}")
                webbrowser.open(target)
                self.voice.speak(f"Opening {app_name}.", callback=_post_launch_unmute)
                return
            
            # ================================================================
            # CASE B: System App / Protocol (no arguments)
            # ================================================================
            has_args = any(arg in target for arg in ["--", "/", " -"])
            
            if not has_args:
                logger.info(f"💻 Case B: System App → {target}")
                os.startfile(target)
                self.voice.speak(f"Opening {app_name}.", callback=_post_launch_unmute)
                return
            
            # ================================================================
            # CASE C: Complex Command (with arguments like Riot Client)
            # ================================================================
            logger.info(f"⚙️ Case C: Complex Command → {target}")
            
            # For Riot Client commands, do NOT suppress output (keeps launcher alive)
            is_riot_client = "riotclient" in target.lower()
            
            if is_riot_client:
                logger.debug("🎮 Riot Client detected - preserving output streams")
                subprocess.Popen(target, shell=True)
            else:
                # For other commands, suppress output
                subprocess.Popen(
                    target,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            self.voice.speak(f"Opening {app_name}.", callback=_post_launch_unmute)
        
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            self.voice.speak(f"Couldn't find {app_name}.", callback=_post_launch_unmute)
    
    def execute_command(self, text):
        """
        HARDCODED-FIRST COMMAND EXECUTION
        Priority 1: System | 2: Media | 3: Lights | 4: Apps | 5: Time | 6: Date |
                 7: Calendar | 8: Weather | 9: Timer | 10: Clip | 11: YouTube | 12: AI
        """
        text_lower = text.lower()
        
        # Wake word check
        wake_words = [
            "linny", "lenny", "lini", "leni", "linnie", "lynny", "lanny", "leave me", "lily",
            "mini", "minny", "minnie", "mimi",
            "dini", "dinny",
            "nini", "ninny", "ni",
            "ginny", "hinny", "finny", "vinny", "winny", "pinny",
            "lhinny",
            "hey linny", "ok linny", "okay linny", "hi linny", "hello linny", "hey"
        ]
        
        if not any(w in text_lower for w in wake_words):
            logger.debug(f"No wake word in: {text}")
            return
        
        logger.info(f"💬 Command: {text}")
        
        # ====================================================================
        # PRIORITY 1: SYSTEM COMMANDS
        # ====================================================================
        
        if any(w in text_lower for w in ["shutdown", "shut down"]):
            logger.info("⚡ System: Shutdown")
            logger.info("💡 Lights: Off")
            self.lights.turn_off()
            self.voice.speak("Shutting down the System.")
            time.sleep(3)
            threading.Timer(3.0, lambda: os.system("shutdown /s /t 0")).start()
            return
        
        if any(w in text_lower for w in ["reboot", "restart", "Reboot", "Restart"]):
            logger.info("⚡ System: Reboot")
            self.voice.speak("Rebooting the System.")
            threading.Timer(3.0, lambda: os.system("shutdown /r /t 0")).start()
            return
        
        if "lock" in text_lower and any(w in text_lower for w in ["computer", "pc"]):
            logger.info("🔒 System: Lock")
            self.voice.speak("Locking the System.")
            threading.Timer(1.0, lambda: ctypes.windll.user32.LockWorkStation()).start()
            return
        
        if "sleep" in text_lower and any(w in text_lower for w in ["computer", "pc"]):
            logger.info("💤 System: Sleep")
            self.voice.speak("Putting the System to sleep.")
            threading.Timer(1.0, lambda: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")).start()
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
        # PRIORITY 3: SMART LIGHT CONTROLS
        # ====================================================================
        
        # Specific Brightness Control (e.g. "Lights to 50%", "Set lights to 20%", "Set brightness to 50%")
        if ("lights" in text_lower or "brightness" in text_lower) and ("%" in text_lower or "percent" in text_lower or "to" in text_lower):
            match = re.search(r'(\d+)', text_lower)
            if match:
                level = int(match.group(1))
                logger.info(f"💡 Lights: Set to {level}%")
                if self.lights.set_brightness(level):
                    self.voice.speak(f"Lights set to {level} percent.")
                else:
                    self.voice.speak("I couldn't set the brightness.")
                return

        # Color Control
        if "color" in text_lower and "lights" in text_lower:
            for color in ["red", "blue", "violet", "green", "warm"]:
                if color in text_lower:
                    logger.info(f"🎨 Lights: Color {color}")
                    if self.lights.set_color(color):
                        self.voice.speak(f"Lights changed to {color}.")
                    else:
                        self.voice.speak(f"I couldn't change the color to {color}.")
                    return
        
        if any(w in text_lower for w in ["turn on lights", "lights on", "turn on the lights", "turn on bulb", "bulb on", "turn on the bulb", "buksan ilaw", "buksan ang ilaw"]):
            logger.info("💡 Lights: On")
            self.lights.turn_on()
            self.voice.speak("Lights turned on.")
            return
        
        if any(w in text_lower for w in ["turn off lights", "lights off", "turn off the lights", "turn off bulb", "bulb off", "turn off the bulb", "patayin ilaw", "patayin ang ilaw", "patay ilaw"]):
            logger.info("💡 Lights: Off")
            self.lights.turn_off()
            self.voice.speak("Lights turned off.")
            return
        
        if "focus mode" in text_lower or "focus" in text_lower:
            logger.info("💡 Lights: Focus Mode")
            self.lights.set_mode("focus")
            self.voice.speak("Focus mode activated.")
            return
        
        if "movie mode" in text_lower or "movie" in text_lower:
            logger.info("💡 Lights: Movie Mode")
            self.lights.set_mode("movie")
            self.voice.speak("Movie mode activated.")
            return
        
        if "gaming mode" in text_lower or "gaming" in text_lower or "game mode" in text_lower:
            logger.info("💡 Lights: Gaming Mode")
            self.lights.set_mode("gaming")
            self.voice.speak("Gaming mode activated.")
            return
             
        # ====================================================================
        # PRIORITY 4: APP LAUNCHER
        # ====================================================================
        
        app_name = None
        for verb in ["open", "launch", "start", "Accio"]:
            if verb in text_lower:
                parts = text_lower.split(verb, 1)
                if len(parts) > 1:
                    app_name = parts[1].strip()
                    break
        
        if app_name:
            for wake_word in wake_words:
                app_name = app_name.replace(wake_word, "").strip()
            
            self._launch_app(app_name)
            return
        
        # ====================================================================
        # PRIORITY 5: TIME
        # ====================================================================
        
        if any(w in text_lower for w in ["time", "oras", "what time"]):
            logger.info("🕐 Time")
            tz = pytz.timezone(self.config.get("timezone", "Asia/Manila"))
            time_str = datetime.now(tz).strftime("%I:%M %p")
            self.voice.speak(f"It is {time_str}.")
            return
        
        # ====================================================================
        # PRIORITY 6: DATE
        # ====================================================================
        
        if any(w in text_lower for w in ["date", "day", "what day", "what is today"]):
            logger.info("📅 Date")
            tz = pytz.timezone(self.config.get("timezone", "Asia/Manila"))
            date_str = datetime.now(tz).strftime("%A, %B %d, %Y")
            self.voice.speak(f"Today is {date_str}.")
            return
        
        # ====================================================================
        # PRIORITY 7: CALENDAR
        # ====================================================================
        
        if any(w in text_lower for w in ["schedule", "calendar", "agenda"]):
            logger.info("📅 Schedule")
            schedule = self.calendar.get_schedule(query=text)
            self.voice.speak(schedule)
            return
        
        # ====================================================================
        # PRIORITY 8: WEATHER
        # ====================================================================
        
        if any(w in text_lower for w in ["weather", "panahon"]):
            logger.info("🌤️ Weather")
            weather = self._get_weather()
            self.voice.speak(weather)
            return
        
        # ====================================================================
        # PRIORITY 9: TIMER
        # ====================================================================
        
        if any(w in text_lower for w in ["timer", "set timer", "pomodoro", "set a timer"]):
            logger.info("⏱️ Timer")
            self._start_timer(text_lower)
            return
        
        # ====================================================================
        # PRIORITY 10: CLIP and SCREENSHOT
        # ====================================================================
        
        if any(w in text_lower for w in ["clip that", "record that"]):
            logger.info("📸 Clip")
            pyautogui.hotkey('alt', 'f10')
            self.voice.speak("Clipped.")
            return
        
        if any(w in text_lower for w in ["screenshot", "take a screenshot", "capture screen", "take screenshot"]):
            logger.info("📸 Screenshot")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            folder_path = Path(self.config.get("screenshot_folder", Path.home() / "Pictures" / "Screenshots"))
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                file_path = folder_path / f"screenshot_{timestamp}.png"
                pyautogui.screenshot(str(file_path))
                time.sleep(1)
                self.voice.speak("Fullscreen screenshot taken.")
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                self.voice.speak("I couldn't take the screenshot.")
            return

        # ====================================================================
        # PRIORITY 11: PLAY ON YOUTUBE
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
            
        if "stop listening" in text_lower:
            logger.info("🛑 Stop Listening Command Received")
            self.voice.speak("Stopping listening. Goodbye!")
            self.toggle_mute()
            if self.tray:
                self.tray.update_state("muted")
            return
        
        # ====================================================================
        # PRIORITY 12: AI BRAIN (FALLBACK)
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
        no_speech_count = 0
        timeout_count = 0
        
        while self.is_listening:
            try:
                # STRICT AUDIO LOCKING
                while self.voice.is_speaking or self.is_muted:
                    time.sleep(0.1)
                
                cycle += 1
                if cycle % 500 == 0:
                    gc.collect()
                
                if source is None:
                    logger.warning("Audio source lost, re-opening...")
                    try:
                        source = self.microphone.__enter__()
                        self._audio_source = source
                        logger.info("✓ Audio source reopened")
                    except Exception as e:
                        logger.error(f"Re-open failed: {e}")
                        time.sleep(1)
                        continue
                
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    
                    # CRITICAL: Discard audio if captured during TTS or while muted
                    if self.voice.is_speaking or self.is_muted:
                        logger.info("🗑️ Discarding audio (TTS/mute active)")
                        continue
                    
                    timeout_count = 0
                        
                except sr.WaitTimeoutError:
                    timeout_count += 1
                    if timeout_count % 10 == 0:
                        logger.info(f"⏱️ Timeout waiting for speech (listening, no sound detected)")
                    continue
                except sr.UnknownValueError:
                    no_speech_count += 1
                    if no_speech_count % 5 == 0:
                        logger.info(f"🔇 No speech detected in audio")
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
                    no_speech_count = 0
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    logger.info(f"✨ Recognized: {text}")
                    threading.Thread(target=self.execute_command, args=(text,), daemon=True).start()
                except sr.UnknownValueError:
                    # Try alternative language (Tagalog/Filipino)
                    try:
                        text = self.recognizer.recognize_google(audio, language='fil-PH')
                        logger.info(f"✨ Recognized (Tagalog): {text}")
                        threading.Thread(target=self.execute_command, args=(text,), daemon=True).start()
                    except sr.UnknownValueError:
                        no_speech_count += 1
                        logger.info("🔇 No speech detected in audio")
                        continue
                except sr.RequestError as e:
                    logger.warning(f"API error: {e}")
                    time.sleep(1)
                    continue
                except Exception as e:
                    logger.exception(f"Recognition error: {e}")
                    continue
                    
            except Exception as e:
                logger.exception(f"[LOOP ERROR] {e}")
                try:
                    self.voice.speak("I encountered a glitch, but I'm back online.")
                except Exception:
                    pass
                time.sleep(0.5)
                continue
    
    def start_listening(self):
        """Start listening with retry logic"""
        if not self.is_listening:
            max_retries = 3
            retry_delay = 1
            
            # Show available microphones
            try:
                mics = sr.Microphone.list_microphone_names()
                logger.info(f"📻 Available microphones: {len(mics)}")
                for i, name in enumerate(mics[:5]):  # Show first 5
                    logger.info(f"    [{i}] {name}")
                if len(mics) > 5:
                    logger.info(f"    ... and {len(mics) - 5} more")
            except Exception as e:
                logger.warning(f"Could not list microphones: {e}")
            
            for attempt in range(max_retries):
                try:
                    self._audio_source = self.microphone.__enter__()
                    logger.info("✓ Audio source opened")
                    
                    # ONE-TIME CALIBRATION (not in loop!)
                    logger.info("📊 Calibrating ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(self._audio_source, duration=1)
                    logger.info("✓ Calibration complete")
                    
                    # OPTIMIZED PARAMETERS for maximum responsiveness
                    self.recognizer.pause_threshold = 0.6  # Faster end-of-speech detection
                    self.recognizer.non_speaking_duration = 0.3  # Tighter silence detection
                    self.recognizer.dynamic_energy_threshold = False  # Use initial calibration
                    self.recognizer.energy_threshold = self.recognizer.energy_threshold  # Keep initial value
                    
                    logger.info(f"✓ Recognizer configured (energy threshold: {self.recognizer.energy_threshold:.1f})")
                    logger.info("✓ Speech recognition: Google Translate (en-US / fil-PH)")
                    break  # Success!
                except Exception as e:
                    logger.warning(f"Audio setup failed (attempt {attempt+1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        logger.error("❌ CRITICAL: Could not initialize microphone after 3 attempts!")
                        try:
                            self.voice.speak("Microphone initialization failed. Please check your audio devices.")
                        except Exception:
                            pass
                        return  # Don't start listener if mic failed
            
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
        self.lights = LightManager(self.config)
        
        # Tray (initialize before LinnyAssistant so it can reference it)
        self.tray = TrayManager(
            on_show=self._show_dashboard,
            on_mute=self._toggle_mute,
            on_exit=self._exit_app
        )
        
        # CORE: LinnyAssistant handles all logic with tray reference
        self.assistant = LinnyAssistant(self.config, self.voice, self.calendar, self.brain, self.lights, self.tray)
        
        # GUI
        if not headless:
            self._setup_gui()
        
        # Start tray
        self.tray.start()
        
        # GLOBAL HOTKEY: Ctrl+Shift+Del for instant mute/interrupt
        try:
            keyboard.add_hotkey('ctrl+shift+del', self._hotkey_interrupt)
            logger.info("✓ Global hotkey registered: Ctrl+Shift+Del")
        except Exception as e:
            logger.warning(f"Could not register global hotkey: {e}")
        
        # High priority
        try:
            psutil.Process(os.getpid()).nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("✓ High priority set")
        except Exception as e:
            logger.warning(f"Priority failed: {e}")
    
    def _load_default_config(self):
        """Load default config from JSON file"""
        try:
            if DEFAULT_CONFIG_FILE.exists():
                with open(DEFAULT_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load default config: {e}")
        
        # Minimal fallback if file doesn't exist
        return {
            "language": "English",
            "timezone": "UTC",
            "user_name": "User",
            "voice_en": "en-US-AriaNeural",
            "voice_tl": "en-US-AriaNeural",
            "groq_api_key": "",
            "gemini_api_key": "",
            "perplexity_api_key": "",
            "smart_bulb_ip": "<BULB_IP>",
            "tapo_email": "",
            "tapo_password": "",
            "app_aliases": {}
        }
    
    def _load_config(self):
        """Load config, use defaults if not found"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Config JSON error: {e}")
                default = self._load_default_config()
                self._save_config_impl(default)
                return default
        else:
            logger.warning(f"Config not found at {CONFIG_FILE}, loading defaults")
            default = self._load_default_config()
            self._save_config_impl(default)
            return default
    
    def _save_config_impl(self, config):
        """Save config"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _save_config(self):
        """Save config"""
        self._save_config_impl(self.config)
    
    def _setup_gui(self):
        """Setup GUI"""
        # Lazy imports - only load GUI libraries when needed
        import customtkinter as ctk
        from PIL import Image, ImageDraw
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("L.I.N.N.Y. v9.4 - Dashboard")
        self.root.geometry("800x700")
        
        # Header
        header = ctk.CTkLabel(self.root, text="L.I.N.N.Y. v9.4", font=("Arial", 24, "bold"))
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
        
        # Smart Bulb IP
        ctk.CTkLabel(settings_frame, text="Smart Bulb IP:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.bulb_ip_entry = ctk.CTkEntry(settings_frame, width=300)
        self.bulb_ip_entry.insert(0, self.config.get("smart_bulb_ip", "<BULB_IP>"))
        self.bulb_ip_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Tapo Email
        ctk.CTkLabel(settings_frame, text="Tapo Email:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.tapo_email_entry = ctk.CTkEntry(settings_frame, width=300)
        self.tapo_email_entry.insert(0, self.config.get("tapo_email", ""))
        self.tapo_email_entry.grid(row=4, column=1, padx=10, pady=5)
        
        # Tapo Password
        ctk.CTkLabel(settings_frame, text="Tapo Password:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.tapo_password_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.tapo_password_entry.insert(0, self.config.get("tapo_password", ""))
        self.tapo_password_entry.grid(row=5, column=1, padx=10, pady=5)
        
        # API Keys
        ctk.CTkLabel(settings_frame, text="Groq API Key:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.groq_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.groq_entry.insert(0, self.config.get("groq_api_key", ""))
        self.groq_entry.grid(row=6, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Gemini API Key:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.gemini_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.gemini_entry.insert(0, self.config.get("gemini_api_key", ""))
        self.gemini_entry.grid(row=7, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Perplexity API Key:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.perplexity_entry = ctk.CTkEntry(settings_frame, width=300, show="*")
        self.perplexity_entry.insert(0, self.config.get("perplexity_api_key", ""))
        self.perplexity_entry.grid(row=8, column=1, padx=10, pady=5)
        
        # Save Button
        save_btn = ctk.CTkButton(settings_frame, text="Save Settings", command=self._save_settings)
        save_btn.grid(row=9, column=0, columnspan=2, pady=10)
        
        # Edit Aliases Button
        edit_btn = ctk.CTkButton(settings_frame, text="Edit App Aliases", command=self._edit_aliases)
        edit_btn.grid(row=10, column=0, columnspan=2, pady=10)
        
        # Control Frame
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=10)
        
        self.mute_btn = ctk.CTkButton(control_frame, text="Mute", command=self._toggle_mute, width=150, fg_color="#2196f3")
        self.mute_btn.pack(side="left", padx=10)
        
        start_btn = ctk.CTkButton(control_frame, text="Start Listening", command=self._start_listening, width=150)
        start_btn.pack(side="left", padx=10)
        
        # Protocol
        self.root.protocol("WM_DELETE_WINDOW", self._hide_dashboard)
    
    def _save_settings(self):
        """Save settings"""
        self.config["user_name"] = self.name_entry.get()
        self.config["language"] = self.lang_var.get()
        self.config["smart_bulb_ip"] = self.bulb_ip_entry.get()
        self.config["tapo_email"] = self.tapo_email_entry.get()
        self.config["tapo_password"] = self.tapo_password_entry.get()
        self.config["groq_api_key"] = self.groq_entry.get()
        self.config["gemini_api_key"] = self.gemini_entry.get()
        self.config["perplexity_api_key"] = self.perplexity_entry.get()
        
        self._save_config()
        
        # Reinit brain and lights
        self.brain = BrainManager(self.config)
        self.assistant.brain = self.brain
        
        self.lights = LightManager(self.config)
        self.assistant.lights = self.lights
        
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
        """Show GUI (create on-demand if in headless mode)"""
        if not hasattr(self, 'root'):
            # GUI was never created (headless mode) - create it now
            logger.info("📊 Creating dashboard on-demand...")
            self._setup_gui()
            logger.info("✓ Dashboard created and shown")
        else:
            # GUI already exists, just show it
            self.root.deiconify()
            self.root.lift()  # Bring to front
            self.root.focus_force()  # Give it focus
            logger.info("✓ Dashboard shown")
    
    def _hide_dashboard(self):
        """Hide GUI"""
        if hasattr(self, 'root'):
            self.root.withdraw()
    
    def _toggle_mute(self):
        """Toggle mute with feedback"""
        is_muted = self.assistant.toggle_mute()
        self.tray.update_state("muted" if is_muted else "listening")
        
        # Update button text and color
        if hasattr(self, 'mute_btn'):
            if is_muted:
                self.mute_btn.configure(text="Unmute", fg_color="#d32f2f")  # Red when muted
            else:
                self.mute_btn.configure(text="Mute", fg_color="#2196f3")    # Blue when active
        
        # Status feedback
        if hasattr(self, 'status_label'):
            status_text = "🔇 Muted" if is_muted else "🎤 Listening"
            self.status_label.configure(text=f"Status: {status_text}")
        
        logger.info(f"🔇 Mute toggled: {is_muted}")
    
    def _start_listening(self):
        """Start listening"""
        self.assistant.start_listening()
        self.tray.update_state("listening")
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Status: Listening...")
    
    def _hotkey_interrupt(self):
        """Global hotkey handler: Instant interrupt + mute toggle"""
        logger.info("⚡ HOTKEY: Ctrl+Shift+Del pressed")
        
        # 1. INSTANT INTERRUPT: Stop any ongoing TTS
        self.voice.stop()
        
        # 2. TOGGLE MUTE
        self._toggle_mute()
    
    def startup_sequence(self):
        """
        OPTIMIZED HYBRID STARTUP SEQUENCE (v9.3):
        1. Lock workstation IMMEDIATELY (~0.3s)
        2. Set high process priority
        3. Wait for audio drivers to initialize (2s)
        4. Start listening (immortal loop)
        5. Async: Fetch weather/calendar, speak greeting
        
        This ensures PC locks before user can interact, while maintaining
        full smart assistant functionality (greeting plays after unlock).
        """
        logger.info("🚀 Starting Linny HYBRID startup sequence...")
        
        try:
            # ================================================================
            # CRITICAL PATH: LOCK IMMEDIATELY (before any delays)
            # ================================================================
            logger.info("🔒 IMMEDIATE LOCK: Locking workstation...")
            try:
                ctypes.windll.user32.LockWorkStation()
                logger.info("✓ Workstation locked in ~0.3s")
            except Exception as e:
                logger.error(f"Failed to lock workstation: {e}")
            
            # ================================================================
            # HIGH PRIORITY: Ensure Linny loads before other startup apps
            # ================================================================
            try:
                p = psutil.Process()
                p.nice(psutil.HIGH_PRIORITY_CLASS)
                logger.info("✓ Process priority set to HIGH")
            except Exception as e:
                logger.warning(f"Could not set high priority: {e}")
            
            # ================================================================
            # CRITICAL: Wait for audio drivers BEFORE starting listener
            # ================================================================
            logger.info("⏳ Waiting 2s for Windows audio drivers...")
            time.sleep(2)
            
            # ================================================================
            # START LISTENING: Immortal loop starts (audio is now ready)
            # ================================================================
            logger.info("🎤 Starting listener...")
            self._start_listening()
            
            # ================================================================
            # ASYNC GREETING: Everything else happens in background
            # ================================================================
            def _async_greeting():
                """Background thread: fetch data + greeting"""
                try:
                    
                    # Get timezone and current time
                    tz = pytz.timezone(self.config.get("timezone", "Asia/Manila"))
                    now = datetime.now(tz)
                    
                    # Build greeting
                    hour = now.hour
                    if 5 <= hour < 12:
                        greeting_prefix = "Good morning"
                    elif 12 <= hour < 18:
                        greeting_prefix = "Good afternoon"
                    else:
                        greeting_prefix = "Good evening"
                    
                    user_name = self.config.get("user_name", "User")
                    greeting = f"{greeting_prefix}, {user_name}."
                    
                    # Format date and time
                    date_str = now.strftime("%A, %B %d")
                    time_str = now.strftime("%I:%M %p")
                    datetime_msg = f"It is {date_str}, at {time_str}."
                    
                    # Get smart schedule (async network call)
                    try:
                        schedule_msg = self.calendar.get_schedule("")
                    except Exception as e:
                        logger.warning(f"Could not fetch schedule: {e}")
                        schedule_msg = "Calendar is offline."
                    
                    # Get weather (async network call)
                    try:
                        weather_msg = self.assistant._get_weather()
                    except Exception as e:
                        logger.warning(f"Could not fetch weather: {e}")
                        weather_msg = ""
                    
                    # Combine all messages
                    full_greeting = f"{greeting} {datetime_msg} {weather_msg} {schedule_msg}"
                    
                    logger.info(f"✨ [ASYNC] Greeting ready: {full_greeting}")
                    
                    # Speak greeting (user will hear this after unlocking)
                    self.voice.speak(full_greeting)
                    
                except Exception as e:
                    logger.error(f"Async greeting error: {e}")
            
            # Launch async greeting thread
            threading.Thread(target=_async_greeting, daemon=True).start()
            logger.info("✓ Async greeting thread launched")
            
            logger.info("✓ HYBRID startup sequence complete (lock: ~0.3s)")
            
        except Exception as e:
            logger.error(f"Startup sequence error: {e}")
            self._start_listening()
    
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
                    time.sleep(1)
            except KeyboardInterrupt:
                self._exit_app()
        else:
            self.root.mainloop()

# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    """Main entry point - runs startup sequence then app"""
    # Set process name for Task Manager
    try:
        # Set console title
        ctypes.windll.kernel32.SetConsoleTitleW("Linny")
        # Set process name for Task Manager display
        try:
            import setproctitle
            setproctitle.setproctitle("Linny")
            logger.info("✓ Process name set to 'Linny'")
        except ImportError:
            logger.info("setproctitle not installed, Task Manager will show 'python'")
    except Exception as e:
        logger.warning(f"Could not set process title: {e}")
    
    headless = "--startup" in sys.argv
    app = LinnyApp(headless=headless)
    
    # Run startup sequence
    app.startup_sequence()
    
    # Run main app loop
    app.run()

if __name__ == "__main__":
    main()
