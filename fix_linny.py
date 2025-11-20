"""
Script to add missing methods to LinnyAssistant class in linny_app.py
This adds: check_wake_word, handle_calendar_query, process_command, start_listening, stop_listening
"""

# Read the file
with open('linny_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where to insert (after listen_once method, before LinnyGUI class)
insert_marker = "class LinnyGUI:"

# The methods to add
methods_to_add = '''    
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
            events = self.calendar_manager.get_upcoming_events(max_results=5, calendar_id=calendar_id)
        elif 'work' in command_lower:
            # Work-specific query
            self.log("Detected: Work calendar query")
            calendar_id = self.calendar_manager.get_calendar_id('Work')
            events = self.calendar_manager.get_upcoming_events(max_results=5, calendar_id=calendar_id)
        else:
            # Default: Merge events from both Primary and School calendars
            self.log("Detected: General calendar query (merging Primary + School)")
            events = self.calendar_manager.get_events_from_multiple_calendars(
                calendar_names=['Primary', 'School'],
                max_results=10
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
        
        # AI Fallback
        if self.model:
            try:
                import random
                
                # Immediate feedback
                thinking_phrase = random.choice(self.thinking_phrases)
                self.speak(thinking_phrase)
                self.log(f"Thinking phrase: {thinking_phrase}")
                
                user_name = self.config.get("user_name", "Zeus")
                
                # Language-specific system prompt
                if language == 'fil-PH':
                    system_prompt = f"""Ikaw si Linny, isang tapat na AI assistant na pinangalanan sa isang minamahal na aso na pumanaw na. 
Ang may-ari mo ay si {user_name}. Ikaw ay matulungin, mainit, at maikli ang sagot.

IMPORTANTE: Sumagot ka sa Tagalog (Filipino). Maging natural at friendly."""
                else:
                    system_prompt = f"""You are Linny, a loyal and intelligent AI assistant named after a beloved dog who passed away. 
You are helpful, warm, and concise. Your owner is {user_name}.

IMPORTANT: Respond in English. Be natural and friendly."""
                
                self.log("Sending query to Gemini AI...")
                response = self.model.generate_content(f"{system_prompt}\\n\\nUser: {command}")
                reply = response.text.strip()
                
                self.log(f"AI Response: {reply}")
                self.speak(reply)
                
            except Exception as e:
                error_msg = str(e)
                self.log(f"AI error: {error_msg}", is_error=True)
                
                if language == 'fil-PH':
                    self.speak("Sorry, may problema ako sa pag-isip")
                else:
                    self.speak("Sorry, I encountered an error")
        else:
            self.log("No AI model available", is_error=True)
            if language == 'fil-PH':
                self.speak("Walang AI brain. I-check mo ang API key sa settings.")
            else:
                self.speak("My AI brain is disconnected. Please check the API key in settings.")
    
    def start_listening(self):
        """Start continuous listening loop for wake word"""
        self.is_listening = True
        self.log("=== Starting listening loop ===")
        
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


'''

# Insert the methods
if insert_marker in content:
    parts = content.split(insert_marker)
    new_content = parts[0] + methods_to_add + "\n\n" + insert_marker + parts[1]
    
    # Write back
    with open('linny_app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Successfully added missing methods to LinnyAssistant class")
    print("  - check_wake_word()")
    print("  - handle_calendar_query()")
    print("  - process_command()")
    print("  - start_listening()")
    print("  - stop_listening()")
else:
    print("✗ Could not find insertion point (LinnyGUI class)")
