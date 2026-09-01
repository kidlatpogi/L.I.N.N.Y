# 🌟 L.I.N.N.Y. (v1.1.0)
### *Loyal Intelligent Neural Network for You*

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/GUI-CustomTkinter-blue?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![TTS](https://img.shields.io/badge/TTS-Microsoft%20Edge%20Neural-0078D7?style=for-the-badge&logo=microsoft-edge&logoColor=white)](https://github.com/rany2/edge-tts)
[![AI](https://img.shields.io/badge/AI%20Brain-Groq%20%7C%20Gemini%20%7C%20Perplexity-orange?style=for-the-badge)](https://groq.com)
[![Smart Home](https://img.shields.io/badge/IoT-Tapo%20%26%20Kasa-00B2A9?style=for-the-badge)](https://github.com/python-kasa/python-kasa)
[![Tests](https://img.shields.io/badge/Tests-PyTest%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)

---

## 📖 Overview

**L.I.N.N.Y.** is an enterprise-grade, modular desktop voice assistant and personal companion designed for Windows. Engineered with a decoupled domain architecture, Linny provides natural human-like voice conversations, smart home lighting control, application automation, daily calendar summaries, weather forecasts, and multi-provider AI reasoning.

---

## 🏛️ Architectural Highlights

```
Linny/
├── linny/
│   ├── audio/                  # Audio input (STT) and output (TTS)
│   │   ├── tts.py              # Dual-engine TTS (Edge Neural + Pyttsx3 SAPI5 fallback)
│   │   └── stt.py              # Background Google Speech Recognition with echo lock
│   ├── core/                   # Domain core
│   │   ├── assistant.py        # Master intent router & command orchestrator
│   │   ├── config.py           # Strongly typed configuration schema with atomic JSON writes
│   │   ├── events.py           # Thread-safe pub/sub Event Bus
│   │   └── logger.py           # Centralized structured logger & UI memory buffer
│   ├── integrations/           # Third-party services & hardware
│   │   ├── ai_brain.py         # Cascading LLM brain (Groq -> Gemini -> Perplexity)
│   │   ├── calendar.py         # Google Calendar OAuth2 client with smart day filtering
│   │   ├── smart_home.py       # Modern python-kasa async Tapo L530E controller
│   │   └── weather.py          # Open-Meteo weather client with TTL caching
│   ├── system/                 # Windows OS management
│   │   ├── launcher.py         # 3-case smart application, URL, and game launcher
│   │   ├── power.py            # Power states, lock, screenshot, and media hotkeys
│   │   └── startup.py          # Windows boot registry and process priority manager
│   ├── ui/                     # Presentation layer
│   │   ├── app.py              # CustomTkinter glassmorphism dashboard
│   │   ├── tray.py             # System tray companion with dynamic state colors
│   │   └── views/              # Modular tabbed views (Overview, AI, Smart Home, Aliases, etc.)
│   └── main.py                 # Application CLI and lifecycle entry point
├── tests/                      # Automated test suite (PyTest)
├── scripts/                    # Windows automation scripts
├── linny_config_default.json   # Base configuration template
└── requirements.txt            # Dependency manifest
```

---

## 🚀 Key Features

### 1. 🎙️ Dual-Engine Speech System
- **Microsoft Edge Neural Voice**: Streams hyper-realistic neural voices (`en-PH-RosaNeural`, `en-US-JennyNeural`, `fil-PH-BlessicaNeural`, etc.) via in-memory Pygame playback.
- **Offline SAPI5 Fallback**: Automatically and seamlessly falls back to offline `pyttsx3` speech synthesis if internet connection drops.
- **Instant Interruption**: Hardware hotkeys and speech recognition auto-mute immediately interrupt output with zero audio file lock collisions.

### 2. 🧠 Cascading Multi-Provider AI Brain
Linny intelligently routes questions based on speed, context, and search intent:
1. **Perplexity Sonar**: Triggered automatically for real-time web search, financial quotes, latest news, and fact-checking.
2. **Groq (Llama 3.3 70B)**: Lightning-fast sub-second responses for natural voice dialogue.
3. **Google Gemini (Gemini 2.0 Flash)**: High-context secondary reasoning for complex prompts.
4. **Local Fallback Heuristics**: Handles time, date, math, and system checks completely offline.

### 3. 💡 Smart Home Lighting (Tapo L530E & Kasa)
- Asynchronous non-blocking control for Tapo and TP-Link Kasa smart bulbs and plugs.
- **Lighting Presets**: `Focus` (6000K, 100%), `Movie` (2500K, 30%), `Gaming` (Purple HSV), `Night` (2200K, 10%), `Relax` (Warm 50%).
- **Color & Brightness**: Full HSV color wheel support and percentage-based brightness adjustments.
- **Error Resilience**: Operates gracefully without blocking UI or voice loops when devices are offline.

### 4. 💻 Modernized CustomTkinter Dashboard
- Sleek dark-mode interface with real-time status indicators (Listening, Speaking, Processing, Muted).
- In-app interactive **App Aliases Table**: Add, browse executables, launch, and delete voice shortcuts directly without opening raw config files.
- Live scrolling activity log and console monitor.
- System Tray minimization with colored status rings (Green = Ready, Blue = Speaking, Red = Muted).

---

## 🗣️ Voice Command Cheatsheet

| Category | Voice Trigger Examples |
| :--- | :--- |
| **Wake Words** | `"Hey Linny"`, `"Linny"`, `"Okay Linny"`, `"Hi Linny"` |
| **Smart Lights** | `"Turn on the lights"`, `"Lights off"`, `"Buksan ang ilaw"`, `"Patayin ang ilaw"`, `"Set lights to 50%"`, `"Focus mode"`, `"Gaming mode"`, `"Change light color to blue"` |
| **App Launcher** | `"Open VS Code"`, `"Launch Spotify"`, `"Open Valorant"`, `"Launch Browser"`, `"Start Discord"` |
| **AI Assistant** | `"Who was Ada Lovelace?"`, `"What is quantum computing?"`, `"Search latest tech news"` |
| **Schedule & Agenda** | `"What is my schedule today?"`, `"What do I have tomorrow?"`, `"Calendar agenda"` |
| **Weather** | `"What's the weather?"`, `"Is it going to rain today?"`, `"Anong panahon ngayon?"` |
| **System & Media** | `"Lock computer"`, `"Shutdown PC"`, `"Take a screenshot"`, `"Clip that"`, `"Next song"`, `"Volume up"`, `"Pause music"` |
| **Timer** | `"Set timer for 15 minutes"`, `"5 minute pomodoro"` |
| **YouTube** | `"Play Bohemian Rhapsody on YouTube"` |
| **Mute / Sleep** | `"Stop listening"`, `"Go to sleep"` |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.10 to 3.13** installed on Windows.
- Working Microphone & Speaker/Headset.

### 2. Clone and Install Dependencies
```powershell
git clone https://github.com/kidlatpogi/L.I.N.N.Y.git
cd Linny
pip install -r requirements.txt
```

### 3. Launch Linny
```powershell
# Launch Desktop GUI Dashboard
python -m linny.main

# Or run via batch script
.\scripts\run_linny.bat
```

### 4. Optional: Windows Startup Configuration
To enable Linny to greet you on Windows boot:
```powershell
.\scripts\enable_startup.bat
```
*(Or toggle "Start on Windows Boot" inside the Settings tab in the dashboard)*

---

## 🧪 Automated Testing

Linny includes a comprehensive test suite covering configuration, AI search intent heuristics, smart device controllers, and audio engines:

```powershell
python -m pytest tests/ -v
```

---

## 📜 License

Distributed under the MIT License. Developed with ❤️ by **Zeus**.