"""
L.I.N.N.Y. 3.0 - Loyal Intelligent Neural Network for You
A voice assistant desktop application with GUI dashboard and system automation.

Version 3.0 Features:
- Cascading Brain Architecture (Groq → Perplexity → Gemini)
- Edge-TTS Neural Voices (High Quality)
- Google Calendar API Integration
- Bilingual Support (English/Tagalog)
- Enhanced Wake Word Detection
"""

import sys
import json
import os
import time
import threading
import webbrowser
import ctypes
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# GUI
import customtkinter as ctk

# AI
import google.generativeai as genai
from groq import Groq
from openai import OpenAI

# Voice
import speech_recognition as sr
import edge_tts
import pygame

# Automation
import pywhatkit

# Google Calendar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.api_core import exceptions  # For handling API quotas
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser as date_parser

# Configuration file path
CONFIG_FILE = Path(__file__).parent / "linny_config.json"
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"

# Google Calendar API Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Default configuration
DEFAULT_CONFIG = {
    "groq_api_key": "",
    "perplexity_api_key": "",
    "gemini_api_key": "",
    "wake_word": "Linny",
    "user_name": "Zeus",
    "fake_lock_enabled": False,
    "microphone_index": None,
    "language": "en-US"  # en-US or fil-PH
}


class BrainManager:
    """
    L.I.N.N.Y. 3.0 Cascading Brain Architecture
    Manages multiple AI models with intelligent routing and fallback logic.
    
    Priority:
    1. Groq (Llama 3.3 70B) - Primary, fast and free
    2. Perplexity (Sonar) - For search/news/price queries
    3. Gemini (1.5 Flash) - Backup fallback
    """
    
    def __init__(self, config, log_callback=None):
        self.config = config
        self.log_callback = log_callback
        
        # Search intent keywords
        self.search_keywords = [
            "search", "price", "news", "who won", "latest", "weather",
            "current", "find", "lookup", "what is", "what's",
            "hanap", "presyo", "balita", "panahon"  # Tagalog equivalents
        ]
        
        # Initialize AI clients
        self.groq_client = None
        self.perplexity_client = None
        self.gemini_client = None
        
        self._initialize_clients()
    
    def log(self, message, is_error=False):
        """Log message with timestamp"""
        if self.log_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = "[ERROR]" if is_error else "[INFO]"
            self.log_callback(f"{timestamp} {prefix} [Brain] {message}")
    
    def _initialize_clients(self):
        """Initialize all available AI clients"""
        # Initialize Groq (Primary)
        groq_key = self.config.get("groq_api_key", "").strip()
        if groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
                self.log("✓ Groq client initialized (Primary)")
            except Exception as e:
                self.log(f"Groq initialization failed: {e}", is_error=True)
        else:
            self.log("⚠ Groq API key not configured")
        
        # Initialize Perplexity (Search)
        perplexity_key = self.config.get("perplexity_api_key", "").strip()
        if perplexity_key:
            try:
                self.perplexity_client = OpenAI(
                    api_key=perplexity_key,
                    base_url="https://api.perplexity.ai"
                )
                self.log("✓ Perplexity client initialized (Search)")
            except Exception as e:
                self.log(f"Perplexity initialization failed: {e}", is_error=True)
        else:
            self.log("⚠ Perplexity API key not configured")
        
        # Initialize Gemini (Backup)
        gemini_key = self.config.get("gemini_api_key", "").strip()
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                # Test the model
                test_response = self.gemini_client.generate_content("Hi")
                self.log("✓ Gemini client initialized (Backup)")
            except Exception as e:
                self.log(f"Gemini initialization failed: {e}", is_error=True)
                self.gemini_client = None
        else:
            self.log("⚠ Gemini API key not configured")
    
    def _detect_search_intent(self, text):
        """Detect if the query requires search/news/current information"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.search_keywords)
    
    def _try_groq(self, prompt):
        """Attempt to get response from Groq"""
        if not self.groq_client:
            return None
        
        try:
            self.log("→ Trying Groq (Llama 3.3 70B)...")
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            reply = response.choices[0].message.content.strip()
            self.log(f"✓ Groq responded ({len(reply)} chars)")
            return reply
        except Exception as e:
            self.log(f"✗ Groq failed: {e}", is_error=True)
            return None
    
    def _try_perplexity(self, prompt):
        """Attempt to get response from Perplexity"""
        if not self.perplexity_client:
            return None
        
        try:
            self.log("→ Trying Perplexity (Sonar)...")
            response = self.perplexity_client.chat.completions.create(
                model="sonar",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response.choices[0].message.content.strip()
            self.log(f"✓ Perplexity responded ({len(reply)} chars)")
            return reply
        except Exception as e:
            self.log(f"✗ Perplexity failed: {e}", is_error=True)
            return None
    
    def _try_gemini(self, prompt):
        """Attempt to get response from Gemini"""
        if not self.gemini_client:
            return None
        
        try:
            self.log("→ Trying Gemini (1.5 Flash)...")
            response = self.gemini_client.generate_content(prompt)
            reply = response.text.strip()
            self.log(f"✓ Gemini responded ({len(reply)} chars)")
            return reply
        except exceptions.ResourceExhausted:
            self.log("✗ Gemini quota exceeded", is_error=True)
            return None
        except Exception as e:
            self.log(f"✗ Gemini failed: {e}", is_error=True)
            return None
    
    def ask_brain(self, text, language="en-US"):
        """
        Main entry point for AI queries with cascading logic.
        
        Flow:
        1. If search intent detected → Try Perplexity first
        2. Else → Try Groq (primary)
        3. If primary fails → Try Gemini (backup)
        4. If backup fails → Try Perplexity (final fallback)
        """
        user_name = self.config.get("user_name", "Zeus")
        
        # Build system prompt
        if language == 'fil-PH':
            system_prompt = f"Persona: Linny (Loyal AI). User: {user_name}. Lang: Tagalog. Brief, warm answer."
        else:
            system_prompt = f"Persona: Linny (Loyal AI). User: {user_name}. Lang: English. Brief, warm answer."
        
        full_prompt = f"{system_prompt}\n\nUser: {text}"
        
        # Detect intent
        is_search_query = self._detect_search_intent(text)
        
        if is_search_query:
            self.log("🔍 Search intent detected")
            # Try Perplexity first for search queries
            reply = self._try_perplexity(full_prompt)
            if reply:
                return reply
            
            # Fallback to Groq
            self.log("⚠ Perplexity unavailable, falling back to Groq")
            reply = self._try_groq(full_prompt)
            if reply:
                return reply
            
            # Final fallback to Gemini
            self.log("⚠ Groq unavailable, falling back to Gemini")
            reply = self._try_gemini(full_prompt)
            if reply:
                return reply
        else:
            # General query: Try Groq first (fast and free)
            reply = self._try_groq(full_prompt)
            if reply:
                return reply
            
            # Fallback to Gemini
            self.log("⚠ Groq unavailable, falling back to Gemini")
            reply = self._try_gemini(full_prompt)
            if reply:
                return reply
            
            # Final fallback to Perplexity
            self.log("⚠ Gemini unavailable, falling back to Perplexity")
            reply = self._try_perplexity(full_prompt)
            if reply:
                return reply
        
        # All models failed
        self.log("✗ All AI models failed", is_error=True)
        if language == 'fil-PH':
            return "Sorry, lahat ng AI models ay hindi available ngayon."
        else:
            return "Sorry, all AI models are currently unavailable."




class GoogleCalendarManager:
    """Manages Google Calendar API authentication and event fetching"""
    
    def __init__(self, credentials_path, token_path, log_callback=None):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.log_callback = log_callback
        self.service = None
        self.creds = None
    
    def log(self, message, is_error=False):
        """Log message with timestamp"""
        if self.log_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = "[ERROR]" if is_error else "[INFO]"
            self.log_callback(f"{timestamp} {prefix} [Calendar] {message}")
    
    def authenticate(self):
        """Authenticate with Google Calendar API using OAuth2"""
        try:
            # Check if credentials.json exists
            if not self.credentials_path.exists():
                self.log("credentials.json not found. Please set up Google Calendar API.", is_error=True)
                return False
            
            # Load existing token if available
            if self.token_path.exists():
                self.log("Loading existing token...")
                self.creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            
            # If no valid credentials, authenticate
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.log("Refreshing expired token...")
                    self.creds.refresh(Request())
                else:
                    self.log("Starting OAuth2 flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for next run
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                self.log("Token saved successfully")
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.creds)
            self.log("✓ Google Calendar authenticated successfully")
            return True
            
        except Exception as e:
            self.log(f"Authentication failed: {e}", is_error=True)
            return False
    
    def list_all_calendars(self):
        """List all available calendars for the authenticated user"""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            self.log("Listing all calendars...")
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            self.log(f"Found {len(calendars)} calendars:")
            for cal in calendars:
                self.log(f"  - {cal.get('summary', 'Unnamed')} (ID: {cal['id']})")
            
            return calendars
            
        except HttpError as e:
            self.log(f"Calendar list API error: {e}", is_error=True)
            return None
        except Exception as e:
            self.log(f"Error listing calendars: {e}", is_error=True)
            return None
    
    def get_calendar_id(self, calendar_name):
        """Get calendar ID by name, fallback to 'primary' if not found"""
        try:
            calendars = self.list_all_calendars()
            
            if not calendars:
                self.log("No calendars found, using 'primary'")
                return 'primary'
            
            # Search for calendar by name (case-insensitive)
            calendar_name_lower = calendar_name.lower()
            for cal in calendars:
                cal_summary = cal.get('summary', '').lower()
                if calendar_name_lower in cal_summary or cal_summary in calendar_name_lower:
                    self.log(f"✓ Found calendar '{cal.get('summary')}' with ID: {cal['id']}")
                    return cal['id']
            
            # Not found, fallback to primary
            self.log(f"Calendar '{calendar_name}' not found, using 'primary'")
            return 'primary'
            
        except Exception as e:
            self.log(f"Error getting calendar ID: {e}", is_error=True)
            return 'primary'
    
    def get_upcoming_events(self, max_results=5, calendar_id='primary', command=''):
        """Fetch upcoming calendar events from a specific calendar with today/tomorrow filtering"""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # Get current time in RFC3339 format
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = None
            
            # Check for "today" or "tomorrow" in command
            command_lower = command.lower()
            
            if 'today' in command_lower or 'ngayon' in command_lower:
                # Set timeMax to end of today (23:59:59)
                end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_max = end_of_day.isoformat() + 'Z'
                self.log(f"Filtering events for TODAY only (until {end_of_day.strftime('%H:%M')})") 
            
            elif 'tomorrow' in command_lower or 'bukas' in command_lower:
                # Set timeMin to tomorrow 00:00:00 and timeMax to tomorrow 23:59:59
                tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                tomorrow_end = tomorrow_start.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_min = tomorrow_start.isoformat() + 'Z'
                time_max = tomorrow_end.isoformat() + 'Z'
                self.log(f"Filtering events for TOMORROW only ({tomorrow_start.strftime('%Y-%m-%d')})") 
            
            # Build API request
            request_params = {
                'calendarId': calendar_id,
                'timeMin': time_min,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            if time_max:
                request_params['timeMax'] = time_max
            
            self.log(f"Fetching events from '{calendar_id}'...")
            events_result = self.service.events().list(**request_params).execute()
            
            events = events_result.get('items', [])
            self.log(f"Found {len(events)} events from '{calendar_id}'")
            return events
            
        except HttpError as e:
            self.log(f"Calendar API error: {e}", is_error=True)
            return None
        except Exception as e:
            self.log(f"Error fetching events: {e}", is_error=True)
            return None
    
    def get_events_from_multiple_calendars(self, calendar_names, max_results=10, command=''):
        """Fetch and merge events from multiple calendars, sorted by time"""
        try:
            all_events = []
            
            for calendar_name in calendar_names:
                # Get calendar ID
                calendar_id = self.get_calendar_id(calendar_name)
                
                # Fetch events (pass command for today/tomorrow filtering)
                events = self.get_upcoming_events(max_results=max_results, calendar_id=calendar_id, command=command)
                
                if events:
                    # Add calendar source to each event for reference
                    for event in events:
                        event['_calendar_source'] = calendar_name
                    all_events.extend(events)
            
            if not all_events:
                self.log("No events found from any calendar")
                return []
            
            # Sort all events by start time
            def get_event_start_time(event):
                start = event['start'].get('dateTime', event['start'].get('date'))
                return date_parser.parse(start)
            
            all_events.sort(key=get_event_start_time)
            
            # Limit to max_results
            all_events = all_events[:max_results]
            
            self.log(f"✓ Merged and sorted {len(all_events)} events from {len(calendar_names)} calendars")
            return all_events
            
        except Exception as e:
            self.log(f"Error merging calendar events: {e}", is_error=True)
            return None
    
    def format_events_for_speech(self, events, language='en-US'):
        """Convert events to natural language for TTS"""
        if not events:
            if language == 'fil-PH':
                return "Wala kang upcoming events sa calendar mo."
            else:
                return "You have no upcoming events on your calendar."
        
        # Build speech text
        if language == 'fil-PH':
            count = len(events)
            speech = f"Mayroon kang {count} upcoming event{'s' if count > 1 else ''}. "
            
            for i, event in enumerate(events, 1):
                summary = event.get('summary', 'No title')
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Parse and format date
                dt = date_parser.parse(start)
                if dt.date() == datetime.now().date():
                    time_str = f"ngayong araw sa {dt.strftime('%I:%M %p')}"
                elif dt.date() == (datetime.now() + timedelta(days=1)).date():
                    time_str = f"bukas sa {dt.strftime('%I:%M %p')}"
                else:
                    time_str = dt.strftime('%B %d sa %I:%M %p')
                
                speech += f"{summary} {time_str}. "
        else:
            count = len(events)
            speech = f"You have {count} upcoming event{'s' if count > 1 else ''}. "
            
            for i, event in enumerate(events, 1):
                summary = event.get('summary', 'No title')
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Parse and format date
                dt = date_parser.parse(start)
                if dt.date() == datetime.now().date():
                    time_str = f"today at {dt.strftime('%I:%M %p')}"
                elif dt.date() == (datetime.now() + timedelta(days=1)).date():
                    time_str = f"tomorrow at {dt.strftime('%I:%M %p')}"
                else:
                    time_str = dt.strftime('%B %d at %I:%M %p')
                
                speech += f"{summary} {time_str}. "
        
        return speech.strip()


class LinnyAssistant:
    """Core voice assistant logic with Edge-TTS and multilingual support"""
    
    def __init__(self, config, status_callback=None, log_callback=None):
        self.config = config
        self.status_callback = status_callback
        self.log_callback = log_callback
        self.is_listening = False
        self.is_speaking = False  # NEW: Prevent self-listening loop
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        # Phonetic aliases for robust wake word detection
        self.phonetic_aliases = [
            'linny',
            'lini',
            'leni',
            'liney',
            'line he',
            'lennie',
            'lenny',
            'lily',
            'lilly',
            'lenny',
            'lany'
        ]
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            self.log("Pygame mixer initialized for audio playback")
        except Exception as e:
            self.log(f"Pygame mixer initialization error: {e}", is_error=True)
        
        # Get thinking phrases based on language
        self.update_thinking_phrases()
        
        # Initialize Google Calendar Manager
        self.calendar_manager = GoogleCalendarManager(
            credentials_path=CREDENTIALS_FILE,
            token_path=TOKEN_FILE,
            log_callback=self.log
        )
        
        # Initialize BrainManager (L.I.N.N.Y. 3.0 Cascading Brain)
        self.brain_manager = BrainManager(self.config, self.log)
    
    def update_thinking_phrases(self):
        """Update thinking phrases based on language setting"""
        language = self.config.get('language', 'en-US')
        
        if language == 'fil-PH':
            self.thinking_phrases = [
                "Sandali lang...",
                "Tingnan ko...",
                "Isipin ko muna...",
                "Antay lang...",
                "Hmm, tignan natin...",
                f"Teka, {self.config.get('user_name', 'Zeus')}..."
            ]
        else:
            self.thinking_phrases = [
                "Let me check...",
                "One moment...",
                "Processing...",
                "On it...",
                "Thinking...",
                "Let me think...",
                "Just a moment...",
                f"Hold on, {self.config.get('user_name', 'Zeus')}..."
            ]
    

    
    def log(self, message, is_error=False):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "[ERROR]" if is_error else "[INFO]"
        full_message = f"{timestamp} {prefix} {message}"
        print(full_message)
        if self.log_callback:
            self.log_callback(full_message)
    
    def update_status(self, message):
        """Update status via callback"""
        self.log(message)
        if self.status_callback:
            self.status_callback(message)
    
    async def async_speak(self, text):
        """Async TTS using Edge-TTS"""
        try:
            # Set speaking flag to prevent self-listening
            self.is_speaking = True
            
            # Select voice based on language
            language = self.config.get('language', 'en-US')
            if language == 'fil-PH':
                voice = 'fil-PH-BlessicaNeural'
            else:
                voice = 'en-PH-RosaNeural'  # Filipino English accent
            
            # Create temporary file for audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_path = temp_file.name
            temp_file.close()
            
            # Generate speech
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
            
            # Play audio using pygame
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Cleanup
            pygame.mixer.music.unload()
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            self.log(f"TTS error: {e}", is_error=True)
        finally:
            # Always clear speaking flag when done
            self.is_speaking = False
    
    def speak(self, text):
        """Thread-safe wrapper for async TTS"""
        def run_async_speak():
            try:
                self.log(f"Speaking: {text}")
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.async_speak(text))
                loop.close()
            except Exception as e:
                self.log(f"Speak thread error: {e}", is_error=True)
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=run_async_speak, daemon=True).start()
    
    def listen_once(self):
        """Listen for a single voice command"""
        mic_index = self.config.get("microphone_index")
        
        if not self.microphone:
            try:
                if mic_index is not None:
                    self.microphone = sr.Microphone(device_index=mic_index)
                    self.log(f"Using microphone index: {mic_index}")
                else:
                    self.microphone = sr.Microphone()
                    self.log("Using default microphone")
            except Exception as e:
                self.log(f"Microphone initialization error: {e}", is_error=True)
                return None
        
        try:
            with self.microphone as source:
                self.update_status("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            self.update_status("Processing speech...")
            
            # Use language-specific recognition
            language = self.config.get('language', 'en-US')
            text = self.recognizer.recognize_google(audio, language=language)
            self.log(f"✓ Heard: '{text}'")
            return text
        
        except sr.WaitTimeoutError:
            self.log("Timeout: No speech detected")
            return None
        except sr.UnknownValueError:
            self.log("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.log(f"Speech recognition API error: {e}", is_error=True)
            return None
        
        def listen_loop():
            while self.is_listening:
                text = self.listen_once()
                if text and self.check_wake_word(text):
                    self.process_command(text)
                time.sleep(0.1)
            self.log("=== Listening loop stopped ===")
        
        threading.Thread(target=listen_loop, daemon=True).start()
        self.update_status("Started listening for wake word")
    
    def stop_listening(self):
        """Stop listening loop"""
        self.is_listening = False
        self.log("Stopping listening loop...")
        self.update_status("Stopped listening")


    
    def check_wake_word(self, text):
        """Check if wake word or any phonetic alias is present in text"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check all phonetic aliases
        for alias in self.phonetic_aliases:
            if alias in text_lower:
                self.log(f"✓ Wake word alias '{alias}' detected in '{text_lower}'")
                return True
        
        self.log(f"✗ No wake word alias found in '{text_lower}'")
        return False
    
    def handle_calendar_query(self, command=''):
        """Handle calendar-related queries with multi-calendar support"""
        language = self.config.get('language', 'en-US')
        
        # Determine which calendars to query based on command
        command_lower = command.lower()
        
        # Check for specific calendar mentions
        if 'school' in command_lower:
            # School-specific query
            self.log("Detected: School calendar query")
            calendar_id = self.calendar_manager.get_calendar_id('School')
            events = self.calendar_manager.get_upcoming_events(max_results=5, calendar_id=calendar_id, command=command)
        elif 'work' in command_lower:
            # Work-specific query
            self.log("Detected: Work calendar query")
            calendar_id = self.calendar_manager.get_calendar_id('Work')
            events = self.calendar_manager.get_upcoming_events(max_results=5, calendar_id=calendar_id, command=command)
        else:
            # Default: Merge events from both Primary and School calendars
            self.log("Detected: General calendar query (merging Primary + School)")
            events = self.calendar_manager.get_events_from_multiple_calendars(
                calendar_names=['Primary', 'School'],
                max_results=10,
                command=command
            )
        
        if events is None:
            # Authentication failed, fallback to opening calendar
            if language == 'fil-PH':
                self.speak("Hindi ko ma-access ang calendar mo. Bubuksan ko na lang ang Google Calendar.")
            else:
                self.speak("I can't access your calendar. Opening Google Calendar instead.")
            
            webbrowser.open("https://calendar.google.com")
            return
        
        # Format and speak events
        speech = self.calendar_manager.format_events_for_speech(events, language)
        self.speak(speech)
    
    def process_command(self, text):
        """Process voice command with priority logic"""
        text_lower = text.lower()
        language = self.config.get('language', 'en-US')
        
        # Remove any phonetic alias from the beginning
        command = text_lower
        for alias in self.phonetic_aliases:
            if command.startswith(alias):
                command = command[len(alias):].strip()
                break
        
        self.log(f"Processing command: '{command}'")
        
        # Calendar commands
        if language == 'fil-PH':
            calendar_keywords = ['schedule', 'calendar', 'ano schedule', 'events']
        else:
            calendar_keywords = ['schedule', 'calendar', 'my schedule', 'upcoming events']
        
        if any(keyword in command for keyword in calendar_keywords):
            self.log("Executing: Calendar query")
            self.handle_calendar_query(command)
            return
        
        # Play music command
        if "play" in command:
            song = command.replace("play", "").strip()
            if song:
                self.log(f"Executing: Play '{song}' on YouTube")
                if language == 'fil-PH':
                    self.speak(f"Hahanapin ko ang {song}...")
                else:
                    self.speak(f"Searching for {song}...")
                time.sleep(0.5)
                try:
                    pywhatkit.playonyt(song)
                    self.log("✓ YouTube opened successfully")
                except Exception as e:
                    self.log(f"YouTube error: {e}", is_error=True)
                    if language == 'fil-PH':
                        self.speak("Sorry, hindi ko ma-play yan")
                    else:
                        self.speak("Sorry, I couldn't play that")
            return
        
        # Shutdown command
        if "shutdown" in command or "shut down" in command:
            self.log("Executing: System shutdown")
            if language == 'fil-PH':
                self.speak("Mag-shutdown na ang system")
            else:
                self.speak("Shutting down the system now")
            try:
                os.system("shutdown /s /t 0")
            except Exception as e:
                self.log(f"Shutdown error: {e}", is_error=True)
            return
        
        # Time command
        if "time" in command or "oras" in command:
            self.log("Executing: Check current time")
            current_time = datetime.now().strftime("%I:%M %p")
            if language == 'fil-PH':
                response = f"Ngayon ay {current_time}"
            else:
                response = f"It is currently {current_time}"
            self.log(f"Time response: {response}")
            self.speak(response)
            return
        
        # Identity command
        if "who are you" in command or "sino ka" in command:
            self.log("Executing: Identity response")
            if language == 'fil-PH':
                response = "Ako si Linny, ang iyong tapat na AI assistant."
            else:
                response = "I am Linny, your loyal intelligent neural network."
            self.log(f"Identity response: {response}")
            self.speak(response)
            return
        
        # AI Fallback (L.I.N.N.Y. 3.0 Cascading Brain)
        try:
            import random
            
            # Immediate feedback
            thinking_phrase = random.choice(self.thinking_phrases)
            self.speak(thinking_phrase)
            self.log(f"Thinking phrase: {thinking_phrase}")
            
            # Use BrainManager for cascading AI logic
            self.log("Querying Cascading Brain...")
            reply = self.brain_manager.ask_brain(command, language)
            
            if reply:
                self.speak(reply)
            else:
                # All models failed
                if language == 'fil-PH':
                    self.speak("Sorry, walang available na AI models ngayon.")
                else:
                    self.speak("Sorry, no AI models are currently available.")
                    
        except Exception as e:
            error_msg = str(e)
            self.log(f"AI error: {error_msg}", is_error=True)
            
            if language == 'fil-PH':
                self.speak("Sorry, may problema ako sa pag-isip")
            else:
                self.speak("Sorry, I encountered an error")

    
    def start_listening(self):
        """Start continuous listening loop for wake word"""
        self.is_listening = True
        self.log("=== Starting listening loop ===")
        
        def listen_loop():
            while self.is_listening:
                # Skip listening if currently speaking (prevent self-listening)
                if self.is_speaking:
                    time.sleep(0.1)
                    continue
                
                text = self.listen_once()
                if text and self.check_wake_word(text):
                    self.process_command(text)
                time.sleep(0.1)
            self.log("=== Listening loop stopped ===")
        
        threading.Thread(target=listen_loop, daemon=True).start()
        self.update_status("Started listening for wake word")
    
    def stop_listening(self):
        """Stop listening loop"""
        self.is_listening = False
        self.log("Stopping listening loop...")
        self.update_status("Stopped listening")




class LinnyGUI:
    """CustomTkinter GUI Dashboard with L.I.N.N.Y. 2.0 Features"""
    
    def __init__(self):
        self.config = self.load_config()
        self.assistant = None
        
        # Setup window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("L.I.N.N.Y. 2.0 Dashboard")
        self.root.geometry("700x900")
        self.root.resizable(False, False)
        
        self.create_widgets()
        self.load_settings_to_gui()
    
    def load_config(self):
        """Load configuration from JSON file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Ensure new fields exist
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"Config load error: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.update_status("Settings saved successfully")
            self.log_to_console("Settings saved to linny_config.json")
        except Exception as e:
            self.update_status(f"Save error: {e}")
            self.log_to_console(f"[ERROR] Save error: {e}")
    
    def get_microphone_list(self):
        """Get list of available microphones"""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            self.log_to_console(f"Found {len(mic_list)} microphones:")
            for i, name in enumerate(mic_list):
                self.log_to_console(f"  [{i}] {name}")
            return mic_list
        except Exception as e:
            self.log_to_console(f"[ERROR] Could not list microphones: {e}")
            return ["Default Microphone"]
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Title
        title = ctk.CTkLabel(
            self.root,
            text="L.I.N.N.Y. 3.0 Dashboard",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title.pack(pady=15)
        
        # Version badge
        version = ctk.CTkLabel(
            self.root,
            text="Cascading Brain • Neural Voice • Calendar",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        version.pack(pady=(0, 10))
        
        # Configuration Frame
        config_frame = ctk.CTkFrame(self.root)
        config_frame.pack(pady=10, padx=30, fill="both", expand=False)
        
        # API Keys Section
        ctk.CTkLabel(
            config_frame, 
            text="AI Models (Groq Required • Perplexity for Search • Gemini Backup)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(15, 10))
        
        # Groq API Key (Primary)
        ctk.CTkLabel(config_frame, text="Groq API Key (Primary):", font=ctk.CTkFont(size=14)).pack(pady=(5, 5))
        self.groq_api_key_entry = ctk.CTkEntry(config_frame, width=500, show="*", placeholder_text="Enter Groq API key")
        self.groq_api_key_entry.pack(pady=5)
        
        # Perplexity API Key (Search)
        ctk.CTkLabel(config_frame, text="Perplexity API Key (Search):", font=ctk.CTkFont(size=14)).pack(pady=(5, 5))
        self.perplexity_api_key_entry = ctk.CTkEntry(config_frame, width=500, show="*", placeholder_text="Enter Perplexity API key")
        self.perplexity_api_key_entry.pack(pady=5)
        
        # Gemini API Key (Backup)
        ctk.CTkLabel(config_frame, text="Gemini API Key (Backup):", font=ctk.CTkFont(size=14)).pack(pady=(5, 5))
        self.gemini_api_key_entry = ctk.CTkEntry(config_frame, width=500, show="*", placeholder_text="Enter Gemini API key")
        self.gemini_api_key_entry.pack(pady=5)
        
        # Wake Word
        ctk.CTkLabel(config_frame, text="Wake Word:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.wake_word_entry = ctk.CTkEntry(config_frame, width=500, placeholder_text="Default: Linny")
        self.wake_word_entry.pack(pady=5)
        
        # User Name
        ctk.CTkLabel(config_frame, text="User Name:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.user_name_entry = ctk.CTkEntry(config_frame, width=500, placeholder_text="Default: Zeus")
        self.user_name_entry.pack(pady=5)
        
        # Language Selector (NEW)
        ctk.CTkLabel(config_frame, text="Language:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.language_var = ctk.StringVar(value="English")
        self.language_menu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.language_var,
            values=["English", "Tagalog"],
            width=500,
            command=self.on_language_change
        )
        self.language_menu.pack(pady=5)
        
        # Microphone Selector
        ctk.CTkLabel(config_frame, text="Microphone:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.microphone_list = self.get_microphone_list()
        mic_options = [f"[{i}] {name}" for i, name in enumerate(self.microphone_list)]
        
        self.microphone_var = ctk.StringVar(value=mic_options[0] if mic_options else "Default")
        self.microphone_menu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.microphone_var,
            values=mic_options,
            width=500
        )
        self.microphone_menu.pack(pady=5)
        
        # Fake Lock Switch
        self.fake_lock_var = ctk.BooleanVar(value=False)
        self.fake_lock_switch = ctk.CTkSwitch(
            config_frame,
            text="Enable Fake Lock on Startup",
            variable=self.fake_lock_var,
            font=ctk.CTkFont(size=14)
        )
        self.fake_lock_switch.pack(pady=10)
        
        # Buttons Frame (Row 1)
        button_frame1 = ctk.CTkFrame(self.root)
        button_frame1.pack(pady=5, padx=30, fill="x")
        
        # Save Button
        self.save_button = ctk.CTkButton(
            button_frame1,
            text="Save Settings",
            command=self.save_settings,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.save_button.pack(side="left", expand=True, padx=5)
        
        # Test Voice Button
        self.test_voice_button = ctk.CTkButton(
            button_frame1,
            text="Test Voice",
            command=self.test_voice,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="purple"
        )
        self.test_voice_button.pack(side="left", expand=True, padx=5)
        
        # Buttons Frame (Row 2)
        button_frame2 = ctk.CTkFrame(self.root)
        button_frame2.pack(pady=5, padx=30, fill="x")
        
        # Setup Calendar Button (NEW)
        self.calendar_button = ctk.CTkButton(
            button_frame2,
            text="Setup Calendar",
            command=self.setup_calendar,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="blue"
        )
        self.calendar_button.pack(side="left", expand=True, padx=5)
        
        # Start/Stop Button
        self.listen_button = ctk.CTkButton(
            button_frame2,
            text="Start Listening",
            command=self.toggle_listening,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="green"
        )
        self.listen_button.pack(side="left", expand=True, padx=5)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            self.root,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=5)
        
        # Log Console
        log_label = ctk.CTkLabel(
            self.root,
            text="Debug Log Console:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        log_label.pack(pady=(10, 5), padx=30, anchor="w")
        
        self.log_console = ctk.CTkTextbox(
            self.root,
            width=640,
            height=250,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_console.pack(pady=(0, 15), padx=30)
        
        # Initial log message
        self.log_to_console("=== L.I.N.N.Y. 3.0 Debug Console ===")
        self.log_to_console("✓ Cascading Brain Architecture (Groq → Perplexity → Gemini)")
        self.log_to_console("✓ Edge-TTS Neural Voice Engine")
        self.log_to_console("✓ Google Calendar Integration")
        self.log_to_console("✓ Bilingual Support (English/Tagalog)")
        self.log_to_console("")
        self.log_to_console("Configure API keys and click 'Start Listening'.")
    
    def log_to_console(self, message):
        """Add message to log console (thread-safe)"""
        def _log():
            self.log_console.configure(state="normal")
            self.log_console.insert("end", message + "\n")
            self.log_console.see("end")
            self.log_console.configure(state="disabled")
        
        self.root.after(0, _log)
    
    def on_language_change(self, choice):
        """Handle language selection change"""
        lang_code = "fil-PH" if choice == "Tagalog" else "en-US"
        self.log_to_console(f"Language changed to: {choice} ({lang_code})")
        
        # Update thinking phrases if assistant is running
        if self.assistant:
            self.assistant.config['language'] = lang_code
            self.assistant.update_thinking_phrases()
    
    def setup_calendar(self):
        """Guide user through calendar setup"""
        if CREDENTIALS_FILE.exists():
            self.log_to_console("✓ credentials.json found!")
            self.log_to_console("Calendar is ready to use.")
            self.log_to_console("Say 'Linny, what's on my calendar?' to test.")
            
            if TOKEN_FILE.exists():
                self.log_to_console("✓ Already authenticated (token.json exists)")
            else:
                self.log_to_console("⚠ First use will open browser for OAuth login")
        else:
            self.log_to_console("✗ credentials.json NOT found!")
            self.log_to_console("")
            self.log_to_console("Setup Instructions:")
            self.log_to_console("1. Go to: https://console.cloud.google.com")
            self.log_to_console("2. Create a project and enable Calendar API")
            self.log_to_console("3. Create OAuth 2.0 credentials")
            self.log_to_console("4. Download credentials.json")
            self.log_to_console("5. Place it in: " + str(Path(__file__).parent))
            self.log_to_console("")
            
            # Open project directory
            try:
                os.startfile(Path(__file__).parent)
                self.log_to_console("✓ Opened project folder")
            except:
                pass
    
    def load_settings_to_gui(self):
        """Load saved settings into GUI fields"""
        # Migrate old api_key to gemini_api_key if needed
        if "api_key" in self.config and not self.config.get("gemini_api_key"):
            self.config["gemini_api_key"] = self.config["api_key"]
            self.log_to_console("Migrated old API key to gemini_api_key")
        
        # Load three API keys
        self.groq_api_key_entry.insert(0, self.config.get("groq_api_key", ""))
        self.perplexity_api_key_entry.insert(0, self.config.get("perplexity_api_key", ""))
        self.gemini_api_key_entry.insert(0, self.config.get("gemini_api_key", ""))
        
        self.wake_word_entry.insert(0, self.config.get("wake_word", "Linny"))
        self.user_name_entry.insert(0, self.config.get("user_name", "Zeus"))
        self.fake_lock_var.set(self.config.get("fake_lock_enabled", False))
        
        # Set language selection
        language = self.config.get("language", "en-US")
        self.language_var.set("Tagalog" if language == "fil-PH" else "English")
        
        # Set microphone selection
        mic_index = self.config.get("microphone_index")
        if mic_index is not None and mic_index < len(self.microphone_list):
            self.microphone_var.set(f"[{mic_index}] {self.microphone_list[mic_index]}")
    
    def save_settings(self):
        """Save GUI settings to config"""
        # Save three API keys
        self.config["groq_api_key"] = self.groq_api_key_entry.get().strip()
        self.config["perplexity_api_key"] = self.perplexity_api_key_entry.get().strip()
        self.config["gemini_api_key"] = self.gemini_api_key_entry.get().strip()
        
        self.config["wake_word"] = self.wake_word_entry.get().strip() or "Linny"
        self.config["user_name"] = self.user_name_entry.get().strip() or "Zeus"
        self.config["fake_lock_enabled"] = self.fake_lock_var.get()
        
        # Save language preference
        lang_choice = self.language_var.get()
        self.config["language"] = "fil-PH" if lang_choice == "Tagalog" else "en-US"
        
        # Extract microphone index
        mic_selection = self.microphone_var.get()
        try:
            mic_index = int(mic_selection.split("]")[0].replace("[", ""))
            self.config["microphone_index"] = mic_index
            self.log_to_console(f"Microphone set to index {mic_index}")
        except:
            self.config["microphone_index"] = None
            self.log_to_console("Using default microphone")
        
        self.save_config()
        
        # Reinitialize assistant with new config
        if self.assistant:
            self.assistant.config = self.config
            self.assistant.brain_manager = BrainManager(self.config, self.assistant.log)
            self.assistant.update_thinking_phrases()
            self.assistant.microphone = None
    
    def test_voice(self):
        """Test Edge-TTS voice output"""
        self.log_to_console("Testing Edge-TTS voice...")
        if not self.assistant:
            self.assistant = LinnyAssistant(self.config, self.update_status, self.log_to_console)
        
        language = self.config.get('language', 'en-US')
        if language == 'fil-PH':
            self.assistant.speak("Kumusta! Ako si Linny. Gumagana ang aking boses.")
        else:
            self.assistant.speak("Hello! I am Linny. My voice is working perfectly.")
    
    def toggle_listening(self):
        """Start or stop listening"""
        if not self.assistant:
            self.assistant = LinnyAssistant(self.config, self.update_status, self.log_to_console)
        
        if not self.assistant.is_listening:
            self.assistant.start_listening()
            self.listen_button.configure(text="Stop Listening", fg_color="red")
        else:
            self.assistant.stop_listening()
            self.listen_button.configure(text="Start Listening", fg_color="green")
    
    def update_status(self, message):
        """Update status label (thread-safe)"""
        def _update():
            self.status_label.configure(text=message)
        
        self.root.after(0, _update)
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def startup_mode():
    """Headless startup mode with fake lock"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except:
            config = DEFAULT_CONFIG.copy()
    else:
        config = DEFAULT_CONFIG.copy()
    
    # Initialize assistant
    assistant = LinnyAssistant(config)
    
    # Wait 5 seconds
    print("[LINNY] Startup mode: Waiting 5 seconds...")
    time.sleep(5)
    
    # Speak greeting
    user_name = config.get("user_name", "Zeus")
    language = config.get("language", "en-US")
    
    if language == 'fil-PH':
        greeting = f"Magandang umaga, {user_name}. Online na ang mga sistema."
    else:
        greeting = f"Good morning, {user_name}. Systems are online."
    
    print(f"[LINNY] {greeting}")
    assistant.speak(greeting)
    
    # Wait for speech to complete
    time.sleep(4)
    
    # Lock workstation
    print("[LINNY] Locking workstation...")
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception as e:
        print(f"[LINNY] Lock error: {e}")
    
    # Continue listening in background
    print("[LINNY] Starting background listening...")
    assistant.start_listening()
    
    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[LINNY] Shutting down...")


def main():
    """Main entry point"""
    if "--startup" in sys.argv:
        startup_mode()
    else:
        app = LinnyGUI()
        app.run()


if __name__ == "__main__":
    main()
