#!/usr/bin/env python3
"""Test pyttsx3 functionality"""

import pyttsx3
import time

print("Initializing pyttsx3...")
engine = pyttsx3.init()

print("Setting properties...")
engine.setProperty('rate', 150)

print("Getting voices...")
voices = engine.getProperty('voices')
print(f"Available voices: {len(voices)}")
for i, voice in enumerate(voices):
    print(f"  [{i}] {voice.name}")

print("\nTesting speech...")
engine.say("Hello, I am Linny. This is a test.")
engine.runAndWait()

print("Test complete!")
