"""
L.I.N.N.Y. v7.0 - Loyal Intelligent Neural Network for You
Non-Blocking Architecture with Hardcoded Command Processing
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
# LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LINNY")

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================
CONFIG_FILE = Path.home() / ".linny" / "linny_config.json"
TOKEN_FILE = Path.home() / ".linny" / "token.json"
CREDENTIALS_FILE = Path("credentials.json")

CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# ============================================================================
# BRAIN MANAGER - Cascading AI Architecture
# ============================================================================
class BrainManager:
    """Manages multiple AI providers with intelligent fallback logic"""
    
    def __init__(self, config):
        self.config = config
        self.groq_client = None
        self.gemini_model = None
        self.perplexity_client = None
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all AI providers"""
        # Groq (Primary - Speed)
        if self.config.get("groq_api_key"):
            try:
                self.groq_client = groq.Groq(api_key=self.config["groq_api_key"])
                logger.info("✓ Groq initialized")
            except Exception as e:
                logger.warning(f"Groq initialization failed: {e}")
        
        # Gemini (Fallback)
        if self.config.get("gemini_api_key"):
            try:
                genai.configure(api_key=self.config["gemini_api_key"])
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✓ Gemini initialized")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")
        
        # Perplexity (Search & Final Fallback)
        if self.config.get("perplexity_api_key"):
            try:
                self.perplexity_client = OpenAI(
                    api_key=self.config["perplexity_api_key"],
                    base_url="https://api.perplexity.ai"
                )
                logger.info("✓ Perplexity initialized")
            except Exception as e:
                logger.warning(f"Perplexity initialization failed: {e}")
    
    def _is_search_intent(self, query):
        """Detect if query requires web search"""
        search_keywords = ["search", "price", "news", "weather", "who won", 
                          "latest", "current", "today's", "what happened"]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in search_keywords)
    
    def _call_groq(self, query, system_prompt):
        """Call Groq API"""
        if not self.groq_client:
            return None
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq failed: {e}")
            return None
    
    def _call_gemini(self, query, system_prompt):
        """Call Gemini API"""
        if not self.gemini_model:
            return None
        
        try:
            full_prompt = f"{system_prompt}\n\nUser: {query}"
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
            return None
    
    def _call_perplexity(self, query, system_prompt):
        """Call Perplexity API"""
        if not self.perplexity_client:
            return None
        
        try:
            response = self.perplexity_client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Perplexity failed: {e}")
            return None
    
    def ask(self, query, user_name="User", language="English"):
        """
        Cascading Brain Logic:
        1. If search intent -> Try Perplexity first
        2. Try Groq (speed)
        3. Try Gemini (fallback)
        4. Try Perplexity (final fallback)
        5. Return offline message
        """
        system_prompt = f"You are Linny, a loyal AI assistant. User: {user_name}. Language: {language}. Be brief and friendly."
        
        is_search = self._is_search_intent(query)
        
        # Step 1: Search Intent - Try Perplexity first
        if is_search:
            logger.info("🔍 Search intent detected, trying Perplexity first...")
            result = self._call_perplexity(query, system_prompt)
            if result:
                logger.info("✓ Perplexity (search) responded")
                return result
        
        # Step 2: Speed - Try Groq
        logger.info("⚡ Trying Groq...")
        result = self._call_groq(query, system_prompt)
        if result:
            logger.info("✓ Groq responded")
            return result
        
        # Step 3: Fallback - Try Gemini
        logger.info("🔄 Trying Gemini...")
        result = self._call_gemini(query, system_prompt)
        if result:
            logger.info("✓ Gemini responded")
            return result
        
        # Step 4: Final Fallback - Try Perplexity (if not already tried)
        if not is_search:
            logger.info("🔄 Final fallback to Perplexity...")
            result = self._call_perplexity(query, system_prompt)
            if result:
                logger.info("✓ Perplexity (fallback) responded")
                return result
        
        # Step 5: All systems offline
        logger.error("❌ All AI systems offline")
        return "I'm sorry, all my systems are currently offline. Please check your API keys and internet connection."

# ============================================================================
# GOOGLE CALENDAR MANAGER - Smart Schedule v2
# ============================================================================
class GoogleCalendarManager:
    """Manages Google Calendar with Smart Schedule v2: Time filtering, end times, ongoing detection"""
    
    def __init__(self, timezone="Asia/Manila"):
        self.service = None
        self.timezone = pytz.timezone(timezone)
        self.school_calendar_id = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), CALENDAR_SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif CREDENTIALS_FILE.exists():
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), CALENDAR_SCOPES
                )
                creds = flow.run_local_server(port=0)
            else:
                logger.warning("No credentials.json found. Calendar disabled.")
                return
            
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        logger.info("✓ Google Calendar authenticated")
        
        # Find "School" calendar
        self._find_school_calendar()
    
    def _find_school_calendar(self):
        """Find the 'School' calendar ID"""
        if not self.service:
            return
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            for calendar in calendar_list.get('items', []):
                if calendar.get('summary', '').lower() == 'school':
                    self.school_calendar_id = calendar['id']
                    logger.info(f"✓ Found 'School' calendar: {self.school_calendar_id}")
                    return
            
            logger.info("'School' calendar not found, using primary")
        except Exception as e:
            logger.warning(f"Could not search for School calendar: {e}")
    
    def get_smart_schedule(self):
        """
        Smart Schedule v2:
        1. Use "School" calendar if found, else 'primary'
        2. Fetch today's events
        3. Filter: Discard if end_time < now, Mark as "Ongoing" if start < now < end
        4. Format with end times: "Event from X to Y"
        5. Auto-switch to tomorrow if today is empty
        """
        if not self.service:
            return "Calendar is not configured."
        
        try:
            now = datetime.now(self.timezone)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Use School calendar or primary
            calendar_id = self.school_calendar_id or 'primary'
            
            # Fetch today's events
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=today_start.isoformat(),
                timeMax=today_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Smart Time Filtering with Ongoing Detection
            upcoming_events = []
            ongoing_events = []
            
            for event in events:
                # Parse start and end times
                start_time_str = event['start'].get('dateTime', event['start'].get('date'))
                end_time_str = event['end'].get('dateTime', event['end'].get('date'))
                
                start_time = date_parser.parse(start_time_str)
                end_time = date_parser.parse(end_time_str)
                
                # Ensure timezone awareness
                if start_time.tzinfo is None:
                    start_time = self.timezone.localize(start_time)
                if end_time.tzinfo is None:
                    end_time = self.timezone.localize(end_time)
                
                # Filter logic
                if end_time < now:
                    # Event is finished - DISCARD
                    continue
                elif start_time < now < end_time:
                    # Event is ongoing
                    ongoing_events.append((event, start_time, end_time))
                else:
                    # Event is upcoming
                    upcoming_events.append((event, start_time, end_time))
            
            # Combine ongoing + upcoming
            all_active_events = ongoing_events + upcoming_events
            
            # If no active events today, fetch tomorrow
            if not all_active_events:
                logger.info("No more schedule for today, fetching tomorrow...")
                tomorrow_start = today_end
                tomorrow_end = tomorrow_start + timedelta(days=1)
                
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=tomorrow_start.isoformat(),
                    timeMax=tomorrow_end.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                tomorrow_events = events_result.get('items', [])
                
                if not tomorrow_events:
                    return "You have no more schedule for today. You have no events tomorrow either."
                
                # Format tomorrow's events with end times
                summary = f"You have no more schedule for today. For tomorrow, you have {len(tomorrow_events)} event{'s' if len(tomorrow_events) > 1 else ''}:\n"
                for event in tomorrow_events[:5]:
                    start_str = event['start'].get('dateTime', event['start'].get('date'))
                    end_str = event['end'].get('dateTime', event['end'].get('date'))
                    
                    start_t = date_parser.parse(start_str)
                    end_t = date_parser.parse(end_str)
                    
                    summary += f"- {event.get('summary', 'Untitled')} from {start_t.strftime('%I:%M %p')} to {end_t.strftime('%I:%M %p')}\n"
                
                return summary.strip()
            
            # Format today's active events with end times
            summary = f"You have {len(all_active_events)} event{'s' if len(all_active_events) > 1 else ''} remaining today:\n"
            
            for event, start_t, end_t in all_active_events[:5]:
                event_name = event.get('summary', 'Untitled')
                
                # Check if ongoing
                if start_t < now < end_t:
                    summary += f"- {event_name} (Ongoing, ends at {end_t.strftime('%I:%M %p')})\n"
                else:
                    summary += f"- {event_name} from {start_t.strftime('%I:%M %p')} to {end_t.strftime('%I:%M %p')}\n"
            
            return summary.strip()
        
        except Exception as e:
            logger.error(f"Calendar error: {e}")
            return "I couldn't access your calendar right now."

# ============================================================================
# VOICE ENGINE - Edge TTS + Pygame
# ============================================================================
class VoiceEngine:
    """Handles TTS with Edge TTS and Pygame playback"""
    
    def __init__(self, voice="en-PH-RosaNeural"):
        self.voice = voice
        pygame.mixer.init()
        self.is_speaking = False
    
    def speak(self, text, callback=None):
        """Speak text asynchronously"""
        def _speak_thread():
            self.is_speaking = True
            try:
                # Generate TTS
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_path = temp_file.name
                temp_file.close()
                
                asyncio.run(edge_tts.Communicate(text, self.voice).save(temp_path))
                
                # Play with pygame
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Cleanup
                pygame.mixer.music.unload()
                os.unlink(temp_path)
                
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                self.is_speaking = False
                if callback:
                    callback()
        
        threading.Thread(target=_speak_thread, daemon=True).start()
    
    def set_voice(self, voice):
        """Change voice"""
        self.voice = voice

# ============================================================================
# SYSTEM TRAY MANAGER
# ============================================================================
class TrayManager:
    """Manages system tray icon with status indicators"""
    
    def __init__(self, on_show_dashboard, on_toggle_mute, on_exit):
        self.icon = None
        self.on_show_dashboard = on_show_dashboard
        self.on_toggle_mute = on_toggle_mute
        self.on_exit = on_exit
        self.current_state = "listening"
    
    def _create_icon_image(self, color):
        """Create colored circle icon"""
        img = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=color)
        return img
    
    def _create_menu(self):
        """Create tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Show Dashboard", self.on_show_dashboard),
            pystray.MenuItem("Toggle Mute", self.on_toggle_mute),
            pystray.MenuItem("Exit", self.on_exit)
        )
    
    def start(self):
        """Start tray icon"""
        image = self._create_icon_image('green')
        self.icon = pystray.Icon("LINNY", image, "L.I.N.N.Y. v6.1", self._create_menu())
        threading.Thread(target=self.icon.run, daemon=True).start()
        logger.info("✓ System tray started")
    
    def update_state(self, state):
        """Update icon color based on state"""
        self.current_state = state
        
        if self.icon:
            color_map = {
                "listening": "green",
                "speaking": "blue",
                "muted": "red"
            }
            color = color_map.get(state, "gray")
            self.icon.icon = self._create_icon_image(color)
    
    def stop(self):
        """Stop tray icon"""
        if self.icon:
            self.icon.stop()

# ============================================================================
# MAIN APPLICATION
# ============================================================================
class LinnyApp:
    """Main L.I.N.N.Y. Application"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.config = self._load_config()
        
        # Initialize components
        self.brain = BrainManager(self.config)
        self.calendar = GoogleCalendarManager(self.config.get("timezone", "Asia/Manila"))
        
        voice = self.config.get("voice_en" if self.config.get("language") == "English" else "voice_tl")
        self.voice = VoiceEngine(voice)
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        self.is_muted = False
        self.is_listening = False
        
        # Non-blocking architecture
        self._audio_source = None  # persistent microphone AudioSource
        self._command_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        
        # GUI
        if not headless:
            self._setup_gui()
        
        # Tray
        self.tray = TrayManager(
            on_show_dashboard=self._show_dashboard,
            on_toggle_mute=self._toggle_mute,
            on_exit=self._exit_app
        )
        self.tray.start()
        
        # Set high priority
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("✓ High priority set")
        except Exception as e:
            logger.warning(f"Could not set high priority: {e}")
    
    def _load_config(self):
        """Load configuration from external file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    user_config = json.load(f)
                logger.info(f"✓ Loaded config from {CONFIG_FILE}")
                return user_config
            except json.JSONDecodeError as e:
                logger.error(f"❌ Config file has invalid JSON: {e}")
                logger.error(f"   Please fix {CONFIG_FILE} and restart")
                sys.exit(1)
        else:
            logger.error(f"❌ Config file not found: {CONFIG_FILE}")
            logger.error(f"   Please create linny_config.json with your settings")
            sys.exit(1)
    
    def _save_config(self):
        """Save configuration"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _setup_gui(self):
        """Setup CustomTkinter GUI"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("L.I.N.N.Y. v6.1 - Dashboard")
        self.root.geometry("800x650")
        
        # Header
        header = ctk.CTkLabel(self.root, text="L.I.N.N.Y. v6.1", font=("Arial", 24, "bold"))
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
        
        # Edit App Aliases Button
        edit_aliases_btn = ctk.CTkButton(settings_frame, text="Edit App Aliases", command=self._edit_app_aliases)
        edit_aliases_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Control Buttons
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=10)
        
        self.mute_btn = ctk.CTkButton(control_frame, text="Mute", command=self._toggle_mute, width=150)
        self.mute_btn.pack(side="left", padx=10)
        
        start_btn = ctk.CTkButton(control_frame, text="Start Listening", command=self._start_listening, width=150)
        start_btn.pack(side="left", padx=10)
        
        # Protocol
        self.root.protocol("WM_DELETE_WINDOW", self._hide_dashboard)
    
    def _save_settings(self):
        """Save settings from GUI"""
        self.config["user_name"] = self.name_entry.get()
        self.config["language"] = self.lang_var.get()
        self.config["groq_api_key"] = self.groq_entry.get()
        self.config["gemini_api_key"] = self.gemini_entry.get()
        self.config["perplexity_api_key"] = self.perplexity_entry.get()
        
        self._save_config()
        
        # Reinitialize components
        self.brain = BrainManager(self.config)
        
        voice = self.config.get("voice_en" if self.config.get("language") == "English" else "voice_tl")
        self.voice.set_voice(voice)
        
        logger.info("✓ Settings saved and applied")
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Status: Settings Saved!")
    
    def _edit_app_aliases(self):
        """Open config file in Notepad for editing app aliases"""
        try:
            if not CONFIG_FILE.exists():
                self._save_config()
            
            subprocess.Popen(['notepad.exe', str(CONFIG_FILE)])
            logger.info("✓ Opened config file for editing")
            logger.info("⚠️  REMINDER: In JSON, backslashes must be doubled (\\\\)")
            
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="Status: Edit config.json and restart to apply")
        except Exception as e:
            logger.error(f"Failed to open config file: {e}")
    
    def _show_dashboard(self):
        """Show GUI dashboard"""
        if hasattr(self, 'root'):
            self.root.deiconify()
    
    def _hide_dashboard(self):
        """Hide GUI dashboard"""
        if hasattr(self, 'root'):
            self.root.withdraw()
    
    def _toggle_mute(self):
        """Toggle mute state"""
        self.is_muted = not self.is_muted
        
        if self.is_muted:
            self.tray.update_state("muted")
            logger.info("🔇 Muted")
            if hasattr(self, 'mute_btn'):
                self.mute_btn.configure(text="Unmute")
        else:
            self.tray.update_state("listening")
            logger.info("🔊 Unmuted")
            if hasattr(self, 'mute_btn'):
                self.mute_btn.configure(text="Mute")
    
    def _exit_app(self):
        """Exit application"""
        logger.info("Exiting L.I.N.N.Y...")
        self.is_listening = False
        self.tray.stop()
        if hasattr(self, 'root'):
            self.root.quit()
        sys.exit(0)
    
    def _get_weather(self):
        """Fetch weather for Dasmariñas, Cavite via Open-Meteo."""
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                "?latitude=14.32&longitude=120.93&current_weather=true&timezone=Asia%2FManila"
            )
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            cw = data.get('current_weather') or {}
            temp = cw.get('temperature')
            code = cw.get('weathercode')
            
            if temp is None:
                return "I couldn't read the temperature."
            
            # Simple WMO code mapping
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
            
            return f"It is {round(temp)} degrees and {condition} in Dasmariñas."
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
            return "I couldn't get the weather right now."
    
    def _start_timer(self, minutes_str):
        """Start a background timer."""
        try:
            import re
            match = re.search(r'(\d+)', minutes_str)
            if match:
                minutes = int(match.group(1))
                def timer_thread():
                    time.sleep(minutes * 60)
                    self.tray.update_state("speaking")
                    self.voice.speak(f"Your {minutes} minute timer is done!", 
                                    lambda: self.tray.update_state("listening"))
                
                threading.Thread(target=timer_thread, daemon=True).start()
                self.tray.update_state("speaking")
                self.voice.speak(f"Timer set for {minutes} minutes.", 
                                lambda: self.tray.update_state("listening"))
            else:
                self.tray.update_state("speaking")
                self.voice.speak("I couldn't understand the duration.", 
                                lambda: self.tray.update_state("listening"))
        except Exception as e:
            logger.error(f"Timer error: {e}")
            self.tray.update_state("speaking")
            self.voice.speak("I couldn't set the timer.", 
                            lambda: self.tray.update_state("listening"))
    
    def _execute_command(self, text):
        """
        HARDCODED-FIRST COMMAND PROCESSING (v7.0 Non-Blocking Architecture)
        Priority: Media > System > Apps > Utilities > AI Brain
        This runs in a background thread, not blocking the listen loop.
        """
        text_lower = text.lower()
        
        # Wake word check
        wake_words = ["linny", "lenny", "lini"]
        if not any(wake in text_lower for wake in wake_words):
            return
        
        logger.info(f"💬 Command received: {text}")
        
        # ========================================================================
        # PRIORITY 1: MEDIA CONTROLS (HIGH PRIORITY - NO AI WASTE)
        # ========================================================================
        
        # Resume / Unpause / Continue / Play Music
        if any(word in text_lower for word in ["resume", "unpause", "continue", "play music"]):
            logger.info("⏯️ Media: Play/Resume")
            try:
                import pyautogui
                pyautogui.press("playpause")
                self.tray.update_state("speaking")
                self.voice.speak("Playing.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Media control error: {e}")
            return
        
        # Pause / Stop Music
        if any(word in text_lower for word in ["pause", "stop music"]):
            logger.info("⏸️ Media: Pause")
            try:
                import pyautogui
                pyautogui.press("playpause")
                self.tray.update_state("speaking")
                self.voice.speak("Paused.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Media control error: {e}")
            return
        
        # Next / Skip
        if any(word in text_lower for word in ["next", "skip", "next song", "skip song", "next track"]):
            logger.info("⏭️ Media: Next")
            try:
                import pyautogui
                pyautogui.press("nexttrack")
                self.tray.update_state("speaking")
                self.voice.speak("Next.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Media control error: {e}")
            return
        
        # Volume Up
        if any(word in text_lower for word in ["volume up", "louder", "turn it up", "increase volume"]):
            logger.info("🔊 Media: Volume Up")
            try:
                import pyautogui
                for _ in range(2):
                    pyautogui.press("volumeup")
                self.tray.update_state("speaking")
                self.voice.speak("Volume up.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Media control error: {e}")
            return
        
        # Volume Down
        if any(word in text_lower for word in ["volume down", "softer", "lower volume", "quieter", "turn it down"]):
            logger.info("🔉 Media: Volume Down")
            try:
                import pyautogui
                for _ in range(2):
                    pyautogui.press("volumedown")
                self.tray.update_state("speaking")
                self.voice.speak("Volume down.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Media control error: {e}")
            return
        
        # Mute
        if "mute" in text_lower and "unmute" not in text_lower:
            logger.info("🔇 Media: Mute")
            try:
                import pyautogui
                pyautogui.press("volumemute")
                self.tray.update_state("speaking")
                self.voice.speak("Muted.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Media control error: {e}")
            return
        
        # ========================================================================
        # PRIORITY 2: SYSTEM COMMANDS
        # ========================================================================
        
        if any(word in text_lower for word in ["shutdown", "shut down"]):
            logger.info("⚡ System: Shutdown")
            self.tray.update_state("speaking")
            self.voice.speak("Shutting down the system.", lambda: self.tray.update_state("listening"))
            threading.Timer(3.0, lambda: os.system("shutdown /s /t 0")).start()
            return
        
        if "lock" in text_lower and any(word in text_lower for word in ["computer", "pc", "workstation"]):
            logger.info("🔒 System: Lock")
            self.tray.update_state("speaking")
            self.voice.speak("Locking your workstation.", lambda: self.tray.update_state("listening"))
            threading.Timer(1.0, lambda: ctypes.windll.user32.LockWorkStation()).start()
            return
        
        # ========================================================================
        # PRIORITY 3: APP LAUNCHER (SMART, NO AI)
        # ========================================================================
        
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
            
            logger.info(f"🚀 Launching app: {app_name}")
            app_aliases = self.config.get("app_aliases", {})
            command = app_aliases.get(app_name)
            
            try:
                if command:
                    os.startfile(command)
                    logger.info(f"✓ Launched {app_name} via alias")
                else:
                    os.startfile(app_name)
                    logger.info(f"✓ Launched {app_name} directly")
                
                self.tray.update_state("speaking")
                self.voice.speak(f"Opening {app_name}.", lambda: self.tray.update_state("listening"))
            except FileNotFoundError:
                logger.warning(f"App not found: {app_name}")
                self.tray.update_state("speaking")
                self.voice.speak(f"I couldn't find {app_name}.", lambda: self.tray.update_state("listening"))
            except Exception as e:
                logger.error(f"Failed to launch {app_name}: {e}")
                self.tray.update_state("speaking")
                self.voice.speak("I couldn't open that application.", lambda: self.tray.update_state("listening"))
            return
        
        # ========================================================================
        # PRIORITY 4: UTILITIES (TIME, CALENDAR, WEATHER, TIMER)
        # ========================================================================
        
        # Time Query
        if any(word in text_lower for word in ["time", "oras"]):
            logger.info("🕐 Time")
            now = datetime.now(pytz.timezone(self.config.get("timezone", "Asia/Manila")))
            time_str = now.strftime("%I:%M %p")
            self.tray.update_state("speaking")
            self.voice.speak(f"It is {time_str}.", lambda: self.tray.update_state("listening"))
            return
        
        # Calendar / Schedule
        if any(word in text_lower for word in ["schedule", "calendar", "agenda", "events"]):
            logger.info("📅 Schedule")
            schedule = self.calendar.get_smart_schedule()
            self.tray.update_state("speaking")
            self.voice.speak(schedule, lambda: self.tray.update_state("listening"))
            return
        
        # Weather
        if any(word in text_lower for word in ["weather", "panahon"]):
            logger.info("🌤️ Weather")
            weather = self._get_weather()
            self.tray.update_state("speaking")
            self.voice.speak(weather, lambda: self.tray.update_state("listening"))
            return
        
        # Timer
        if "timer" in text_lower:
            logger.info("⏱️ Timer")
            self._start_timer(text_lower)
            return
        
        # Play on YouTube (Special case, not AI)
        if "play" in text_lower:
            song_name = text_lower
            for wake_word in wake_words:
                song_name = song_name.replace(wake_word, "")
            song_name = song_name.replace("play", "").strip()
            song_name = song_name.replace("on youtube", "").strip()
            
            if song_name and len(song_name) > 2:
                logger.info(f"🎵 YouTube: {song_name}")
                try:
                    pywhatkit.playonyt(song_name)
                    self.tray.update_state("speaking")
                    self.voice.speak(f"Playing {song_name}.", lambda: self.tray.update_state("listening"))
                except Exception as e:
                    logger.error(f"YouTube error: {e}")
                    self.tray.update_state("speaking")
                    self.voice.speak("I couldn't play that.", lambda: self.tray.update_state("listening"))
                return
        
        # ========================================================================
        # PRIORITY 5: AI BRAIN (FALLBACK ONLY)
        # ========================================================================
        
        logger.info("🤖 Fallback to AI Brain")
        response = self.brain.ask(
            text,
            user_name=self.config.get("user_name", "User"),
            language=self.config.get("language", "English")
        )
        self.tray.update_state("speaking")
        self.voice.speak(response, lambda: self.tray.update_state("listening"))
    
    def _listen_loop(self):
        """Robust non-blocking listening loop - persistent audio source, immediate thread dispatch."""
        logger.info("🎤 Listening started (robust mode)...")
        source = self._audio_source
        cycle_count = 0
        
        while self.is_listening:
            try:
                # Quick skip if muted (don't block, small sleep to avoid spin)
                if self.is_muted:
                    time.sleep(0.05)
                    continue
                
                # Memory optimization
                cycle_count += 1
                if cycle_count % 100 == 0:
                    gc.collect()
                    logger.debug(f"🧹 Cycle {cycle_count}")
                
                if source is None:
                    logger.warning("Audio source lost, attempting to re-open...")
                    try:
                        source = self.microphone.__enter__()
                        self._audio_source = source
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    except Exception as e:
                        logger.error(f"Could not re-open audio: {e}")
                        time.sleep(1)
                        continue
                
                try:
                    # Capture audio (timeout: don't wait forever)
                    logger.debug("⏺️ Listening for audio...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    logger.debug("✅ Audio captured")
                    
                except sr.WaitTimeoutError:
                    logger.debug("⏳ Timeout (no speech)")
                    continue
                except sr.UnknownValueError:
                    logger.debug("🔇 Could not understand")
                    continue
                except sr.RequestError as e:
                    logger.warning(f"Recognition error: {e}")
                    continue
                except Exception as e:
                    logger.exception(f"Audio capture error: {e}")
                    time.sleep(0.5)
                    continue
                
                # Recognize speech (in background thread to avoid blocking loop)
                try:
                    logger.debug("🔄 Recognizing...")
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"✨ Recognized: {text}")
                    
                    # FIRE-AND-FORGET: Spawn command thread, loop resumes immediately
                    self._command_executor.submit(self._execute_command, text)
                    logger.debug("→ Command thread dispatched")
                    
                except sr.UnknownValueError:
                    logger.debug("🔇 No recognizable speech")
                    continue
                except sr.RequestError as e:
                    logger.warning(f"Recognition service error: {e}")
                    time.sleep(1)
                    continue
                except Exception as e:
                    logger.exception(f"Recognition error: {e}")
                    continue
                    
            except Exception as e:
                # IMMORTAL LOOP: catch-all, log, continue
                logger.exception(f"[LISTEN LOOP ERROR] {e}")
                try:
                    self.tray.update_state("speaking")
                    self.voice.speak("I encountered a glitch, but I'm back online.", 
                                    lambda: self.tray.update_state("listening"))
                except Exception:
                    pass
                time.sleep(0.5)
                continue
    
    def _start_listening(self):
        """Start listening: open mic once, calibrate once, spawn daemon thread."""
        if not self.is_listening:
            # Open audio source once (persistent)
            try:
                self._audio_source = self.microphone.__enter__()
                logger.info("✓ Audio source opened (persistent)")
                
                # Calibrate once
                self.recognizer.adjust_for_ambient_noise(self._audio_source, duration=1)
                logger.info("✓ Ambient noise calibrated")
                
                # Responsive recognizer
                self.recognizer.pause_threshold = 0.8
                self.recognizer.dynamic_energy_threshold = False
                logger.info("✓ Recognizer configured")
            except Exception as e:
                logger.warning(f"Audio setup warning: {e}")
                # Still try to proceed
            
            self.is_listening = True
            threading.Thread(target=self._listen_loop, daemon=True).start()
            logger.info("✓ Listening thread started")
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="Status: Listening...")
    
    def startup_sequence(self):
        """Execute startup sequence for --startup flag"""
        logger.info("🚀 Executing startup sequence...")
        
        # Hide GUI
        if hasattr(self, 'root'):
            self.root.withdraw()
        
        # Greeting
        tz = pytz.timezone(self.config.get("timezone", "Asia/Manila"))
        current_hour = datetime.now(tz).hour
        
        if current_hour < 12:
            greeting = "Good morning"
        elif current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        user_name = self.config.get("user_name", "User")
        greeting_msg = f"{greeting}, {user_name}. LINNY systems online."
        
        self.voice.speak(greeting_msg)
        
        # Wait for greeting to finish
        while self.voice.is_speaking:
            pygame.time.Clock().tick(10)
        
        # Read schedule
        schedule = self.calendar.get_smart_schedule()
        self.voice.speak(schedule)
        
        # Wait for schedule to finish
        while self.voice.is_speaking:
            pygame.time.Clock().tick(10)
        
        # Lock workstation
        logger.info("🔒 Locking workstation...")
        ctypes.windll.user32.LockWorkStation()
        
        # Memory optimization - cleanup after startup
        gc.collect()
        logger.info("🧹 Startup memory cleanup complete")
        
        # Start listening
        self._start_listening()
    
    def run(self):
        """Run the application"""
        if self.headless:
            # Headless mode - just keep alive
            try:
                while True:
                    pygame.time.Clock().tick(1)
            except KeyboardInterrupt:
                self._exit_app()
        else:
            # GUI mode
            self.root.mainloop()

# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    """Main entry point"""
    headless = "--startup" in sys.argv
    
    app = LinnyApp(headless=headless)
    
    if headless:
        app.startup_sequence()
    else:
        app._start_listening()
    
    app.run()

if __name__ == "__main__":
    main()
