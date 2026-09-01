# 🌟 L.I.N.N.Y. (v1.1.0)
### *Loyal Intelligent Neural Network for You*
> **Desktop AI Voice Assistant & Smart IoT Automation Suite for Windows**

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter%20Dark%20Mode-blue?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Neural TTS](https://img.shields.io/badge/TTS-Microsoft%20Edge%20Neural-0078D7?style=for-the-badge&logo=microsoft-edge&logoColor=white)](https://github.com/rany2/edge-tts)
[![AI Orchestration](https://img.shields.io/badge/AI%20Brain-Groq%20%7C%20Gemini%20%7C%20Perplexity-FF6F00?style=for-the-badge)](https://groq.com)
[![IoT Protocol](https://img.shields.io/badge/IoT-Tapo%20KLAP%20%26%20Kasa-00B2A9?style=for-the-badge)](https://github.com/python-kasa/python-kasa)
[![Test Suite](https://img.shields.io/badge/Tests-PyTest%2019%2F19%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com)

---

## 📖 Executive Summary & What is LINNY?

**L.I.N.N.Y.** (*Loyal Intelligent Neural Network for You*) is an enterprise-grade, high-performance desktop voice assistant and intelligent ambient computing system engineered in Python. Designed with a clean domain-driven architecture, Linny unifies real-time speech recognition, lifelike neural voice synthesis, multi-model AI reasoning, local smart home IoT automation, Google Calendar scheduling, high-precision weather forecasts, and native Windows OS automation into a sleek, 0ms-latency charcoal dark mode dashboard.

---

## 📸 Interface & Visual Showcase

| Overview Dashboard | AI Studio Multi-Model Playground |
| :---: | :---: |
| ![Overview](assets/screenshots/overview.png) | ![AI Studio](assets/screenshots/ai_studio.png) |
| *0ms reactive dashboard with greeting, weather, and instant action triggers.* | *Real-time LLM sandbox with temperature controls and cascading fallback.* |

| Smart Lighting IoT Controls | Application Shortcuts & Launcher |
| :---: | :---: |
| ![Smart Lighting](assets/screenshots/smart_lighting.png) | ![App Shortcuts](assets/screenshots/app_shortcuts.png) |
| *Hardware-debounced Tapo/Kasa KLAP controller with real-time diagnostics.* | *Custom executable, URL, and shell alias registry with zero-lag launching.* |

| Calendar Agenda | Preferences & System Config |
| :---: | :---: |
| ![Calendar](assets/screenshots/calendar.png) | ![Preferences](assets/screenshots/preferences.png) |
| *Google Calendar OAuth2 integration with agenda summaries.* | *Centralized settings, neural voice picker, and coordinate geocoding.* |

| Live Diagnostic Console |
| :---: |
| ![Live Console](assets/screenshots/live_console.png) |
| *Thread-safe circular memory logging stream for real-time auditability.* |

---

## 🚀 Key Technical Features

### 🎙️ 1. Intelligent Speech Recognition & Natural Phrase Capture
- **Non-blocking Audio Streaming**: Built on `speech_recognition` with adaptive ambient noise calibration.
- **Natural Voice Parsing**: Configured with extended phrase duration (`phrase_time_limit=12.0s`) and tuned thresholds (`pause_threshold=1.2s`, `non_speaking_duration=0.8s`) to capture multi-word commands without premature cutoff.
- **Direct Intent Routing**: Seamlessly recognizes both wake-word-prefixed commands (*"Hey Linny open Brave"*, *"Hey open Spotify"*) and direct action commands (*"Weather"*, *"Current time"*, *"Lights on"*, *"Pause music"*).

### 🔊 2. Dual-Engine Neural Voice Synthesis (TTS)
- **Primary Engine**: Microsoft Edge Neural TTS (`edge-tts`) using high-definition neural voices (`en-PH-RosaNeural`, `en-US-JennyNeural`, etc.) streamed asynchronously to an in-memory `pygame.mixer` buffer.
- **Local Offline Fallback**: Windows SAPI5 (`pyttsx3`) ensures voice functionality even when offline.
- **Microphone Echo Cancellation Lock**: Automatically mutes speech listening during TTS playback to prevent self-triggering loops.

### 💡 3. High-Performance Smart Home IoT Automation
- **Persistent Asyncio Event Loop**: Kasa and Tapo smart device operations run on a dedicated daemon event loop thread (`SmartHomeEventLoop`), eliminating Tkinter UI thread freezes.
- **Tapo Protocol & Device Account Compatibility**: Full support for Tapo L535E/L530E multicolor bulbs, P100/P110 smart plugs, and legacy Kasa devices over local HTTP Port 80 KLAP.
- **Hardware-Debounced Slider & Request Coalescing**: Sliders feature a 200ms UI debounce combined with asynchronous backend request coalescing, preventing smart bulb hardware from being overwhelmed during rapid slider adjustments.

### 🧠 4. Cascading Multi-Provider AI Brain
- **Failover Routing**: Queries cascade seamlessly across **Groq** (`llama-3.3-70b-versatile`), **Google Gemini** (`gemini-2.0-flash`), and **Perplexity AI** (`sonar-pro`).
- **Autonomous Search Intent Detection**: Automatically queries live web results when questions involve current events or sports scores.
- **Offline Fallback**: Responds with structured local intelligence if network connectivity is unavailable.

### ⚡ 5. Native Windows Automation & System Power
- **Smart App Launcher**: 3-tier resolver supporting web URLs, direct binaries via `os.startfile`, and complex CLI commands via detached `subprocess.Popen`.
- **Media Controls**: PyAutoGUI-driven multimedia keys for play, pause, track skipping, and volume adjustment.
- **Workstation Security**: High-speed Windows API lock (`ctypes.windll.user32.LockWorkStation`), full-resolution screenshot capture, and GeForce/Xbox Instant Replay clipping.

---

## 🏛️ System Architecture

```
Linny/
├── assets/                     # Portfolio media & visual assets
│   └── screenshots/            # High-resolution UI screenshots
├── linny/                      # Core application package
│   ├── audio/                  # Audio input & output subsystems
│   │   ├── stt.py              # SpeechListener with adaptive thresholds & echo lock
│   │   └── tts.py              # Asynchronous Edge Neural TTS + SAPI5 fallback
│   ├── core/                   # Domain core & orchestration
│   │   ├── assistant.py        # Master intent router & voice controller
│   │   ├── config.py           # Strongly typed LinnyConfig with atomic JSON persistence
│   │   ├── events.py           # Thread-safe pub/sub EventBus
│   │   └── logger.py           # Structured rotating logger & UI memory buffer
│   ├── integrations/           # External API & hardware adapters
│   │   ├── ai_brain.py         # Cascading LLM client (Groq -> Gemini -> Perplexity)
│   │   ├── calendar.py         # Google Calendar OAuth2 client
│   │   ├── smart_home.py       # Non-blocking Tapo/Kasa KLAP device manager
│   │   └── weather.py          # Open-Meteo weather client with TTL caching
│   ├── system/                 # Windows OS operations
│   │   ├── launcher.py         # Intelligent process, game, and URL launcher
│   │   ├── power.py            # Power states, lock workstation, screenshot & media keys
│   │   └── startup.py          # Windows Registry auto-start & process priority
│   └── ui/                     # Presentation layer
│       ├── app.py              # CustomTkinter glassmorphism master window (0ms tab switching)
│       ├── tray.py             # System tray companion with dynamic state colors
│       └── views/              # Modular charcoal-themed view components
│           ├── ai_view.py          # AI Studio LLM playground
│           ├── calendar_view.py    # Google Calendar schedule viewer
│           ├── logs_view.py        # Live console diagnostic viewer
│           ├── overview_view.py    # Master overview dashboard
│           ├── settings_view.py    # System preferences & geocoding
│           ├── shortcuts_view.py   # App & URL shortcuts manager
│           └── smarthome_view.py   # Smart lighting scanner & controls
├── scripts/                    # Management scripts
│   ├── enable_startup.bat      # Enable auto-start on Windows boot
│   ├── disable_startup.bat     # Remove auto-start from registry
│   └── run_linny.bat           # One-click application launcher
├── tests/                      # Automated test suite (19 unit tests)
│   ├── test_brain.py           # AI brain routing tests
│   ├── test_commands.py        # Voice intent parsing tests
│   ├── test_config.py          # Config serialization tests
│   ├── test_launcher.py        # App launcher tests
│   ├── test_smart_home.py      # Smart device manager tests
│   ├── test_tts.py             # Voice engine synthesis tests
│   └── test_weather.py         # Weather geocoding tests
├── linny_config_default.json   # Base configuration template
└── requirements.txt            # Project dependencies
```

---

## 🛠️ Installation & Getting Started

### Prerequisites
- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Version `3.10`, `3.11`, `3.12`, or `3.13`
- **Microphone & Speakers / Headset**

### 1. Clone Repository
```bash
git clone https://github.com/kidlatpogi/L.I.N.N.Y.git
cd L.I.N.N.Y
```

### 2. Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Launch Linny
```powershell
.\scripts\run_linny.bat
# Or directly via Python:
python -m linny.main
```

---

## 🗣️ Supported Voice Commands

| Intent Category | Example Voice Commands | System Action |
| :--- | :--- | :--- |
| **App Launching** | `"Hey open Brave"`, `"Open Spotify"`, `"Launch Discord"`, `"Open VS Code"`, `"Open Valorant"` | Launches executable, game, or web application |
| **Weather** | `"What is the weather"`, `"Weather forecast"`, `"Tell me the weather"`, `"Temperature"` | Announces high-precision weather conditions & temperature |
| **Time & Date** | `"What time is it"`, `"Current time"`, `"What is the date today"`, `"Time check"` | Announces local time/date in configured timezone |
| **Schedule** | `"What's on my schedule"`, `"Calendar agenda"`, `"What do I have today"` | Synthesizes upcoming Google Calendar appointments |
| **Smart Lights** | `"Turn on the lights"`, `"Lights off"`, `"Set brightness to 50%"`, `"Color blue"`, `"Focus mode"` | Sends non-blocking KLAP commands to Tapo/Kasa devices |
| **Media Playback** | `"Pause music"`, `"Resume"`, `"Next song"`, `"Previous track"`, `"Volume up"`, `"Mute audio"` | Controls Windows media playback keys |
| **YouTube** | `"Play [song/artist] on YouTube"` | Searches YouTube and launches playback in browser |
| **Screen Capture** | `"Take a screenshot"`, `"Clip that"` | Saves full-resolution PNG or triggers GeForce replay clip |
| **Timers** | `"Set a timer for 10 minutes"` | Starts background timer with voice alarm upon completion |
| **System Power** | `"Lock PC"`, `"Shutdown PC"`, `"Restart PC"`, `"Sleep PC"` | Locks workstation, restarts, or shuts down system |
| **AI Brain** | Any conversational question (e.g., *"Who was Ada Lovelace?"*, *"Tell me a joke"*) | Routes query to Groq Llama 3.3 / Gemini / Perplexity |

---

## 🧪 Automated Testing & Verification

Linny includes a comprehensive test suite covering all domains, intent parsers, and external integrations:

```powershell
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1
collected 19 items

tests/test_brain.py::test_search_intent_detection PASSED                 [  5%]
tests/test_brain.py::test_offline_fallback PASSED                        [ 10%]
tests/test_commands.py::test_wake_word_extraction PASSED                 [ 15%]
tests/test_commands.py::test_app_launch_intent PASSED                    [ 21%]
tests/test_commands.py::test_weather_intent PASSED                       [ 26%]
tests/test_commands.py::test_time_and_date_intent PASSED                 [ 31%]
tests/test_commands.py::test_schedule_intent PASSED                      [ 36%]
tests/test_commands.py::test_smart_lights_intent PASSED                  [ 42%]
tests/test_commands.py::test_media_controls_intent PASSED                [ 47%]
tests/test_config.py::test_default_config_fields PASSED                  [ 52%]
tests/test_config.py::test_dict_serialization PASSED                     [ 57%]
tests/test_launcher.py::test_alias_resolution PASSED                     [ 63%]
tests/test_launcher.py::test_empty_launch PASSED                         [ 68%]
tests/test_smart_home.py::test_color_presets_coverage PASSED             [ 73%]
tests/test_smart_home.py::test_offline_device_graceful PASSED            [ 78%]
tests/test_tts.py::test_voice_engine_init PASSED                         [ 84%]
tests/test_tts.py::test_voice_engine_stop PASSED                         [ 89%]
tests/test_weather.py::test_weather_fetch_structure PASSED               [ 94%]
tests/test_weather.py::test_weather_summary_text PASSED                  [100%]

======================= 19 passed, 3 warnings in 6.73s ========================
```

---

## 📄 License & Attribution

Designed and developed by **kidlatpogi** as an open-source, portfolio-grade intelligent voice companion for Windows. Distributed under the MIT License.