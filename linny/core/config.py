"""
Configuration management with strong typing, JSON validation, and atomic writes.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict

from .logger import get_logger

logger = get_logger("config")

USER_CONFIG_DIR = Path.home() / ".linny"
USER_CONFIG_FILE = USER_CONFIG_DIR / "linny_config.json"
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_FILE = WORKSPACE_ROOT / "linny_config_default.json"


@dataclass
class LinnyConfig:
    # User Profile & Localization
    user_name: str = "Zeus"
    language: str = "English"
    timezone: str = "Asia/Manila"

    # Audio & Voice Engine
    voice_en: str = "en-PH-RosaNeural"
    voice_tl: str = "fil-PH-BlessicaNeural"
    tts_engine: str = "edge"  # "edge" (with automatic pyttsx3 fallback) or "pyttsx3"
    tts_rate: int = 150
    tts_volume: float = 1.0
    microphone_index: int | None = None
    hotkey: str = "ctrl+shift+del"

    # AI Service API Keys
    groq_api_key: str = ""
    gemini_api_key: str = ""
    perplexity_api_key: str = ""

    # Smart Home (Kasa / Tapo L530E)
    smart_bulb_enabled: bool = True
    smart_bulb_ip: str = "192.168.18.12"
    smart_bulb_family: str = "SMART.TAPOBULB"
    tapo_email: str = ""
    tapo_password: str = ""

    # System & App Launcher
    screenshot_folder: str = str(Path.home() / "Pictures" / "Screenshots")
    lock_on_startup: bool = False
    app_aliases: Dict[str, str] = field(default_factory=lambda: {
        "code": "code",
        "vs code": "C:\\Users\\Zeus\\AppData\\Local\\Programs\\Microsoft VS Code\\code.exe",
        "browser": "C:\\Users\\Zeus\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "brave": "C:\\Users\\Zeus\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "spotify": "spotify:",
        "apple music": "https://music.apple.com/us/new",
        "calculator": "calc",
        "notepad": "notepad",
        "terminal": "wt",
        "files": "explorer",
        "explorer": "explorer",
        "word": "winword",
        "teams": "msteams:",
        "microsoft teams": "msteams:",
        "discord": "C:\\Users\\Zeus\\AppData\\Local\\Discord\\Update.exe --processStart Discord.exe",
        "antigravity": "C:\\Users\\Zeus\\AppData\\Local\\Programs\\Antigravity\\Antigravity.exe",
        "valorant": "E:\\GAMES\\Riot Games\\Riot Client\\RiotClientServices.exe --launch-product=valorant --launch-patchline=live",
        "league": "E:\\GAMES\\Riot Games\\Riot Client\\RiotClientServices.exe --launch-product=league_of_legends --launch-patchline=live",
        "lol": "E:\\GAMES\\Riot Games\\Riot Client\\RiotClientServices.exe --launch-product=league_of_legends --launch-patchline=live",
    })

    # Weather Location
    weather_city: str = "Silang, Cavite"
    weather_latitude: float = 14.2167
    weather_longitude: float = 120.9833

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LinnyConfig:
        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


def get_default_config_dict() -> Dict[str, Any]:
    """Load default config from workspace json file or fall back to dataclass defaults."""
    if DEFAULT_CONFIG_FILE.exists():
        try:
            with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read {DEFAULT_CONFIG_FILE}: {e}")
    return LinnyConfig().to_dict()


def load_config() -> LinnyConfig:
    """Load LinnyConfig from user home directory, creating it from defaults if missing."""
    default_dict = get_default_config_dict()

    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                user_dict = json.load(f)
                # Merge defaults with user settings so new keys are automatically added
                merged = {**default_dict, **user_dict}
                # Preserve and merge app_aliases
                if "app_aliases" in default_dict and "app_aliases" in user_dict:
                    merged["app_aliases"] = {**default_dict["app_aliases"], **user_dict["app_aliases"]}
                return LinnyConfig.from_dict(merged)
        except Exception as e:
            logger.error(f"Error loading {USER_CONFIG_FILE}: {e}. Restoring defaults.")

    # Create config file with defaults
    config = LinnyConfig.from_dict(default_dict)
    save_config(config)
    return config


def save_config(config: LinnyConfig) -> bool:
    """Safely and atomically persist LinnyConfig to JSON."""
    try:
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = config.to_dict()

        # Atomic write using a temp file
        temp_fd, temp_path = tempfile.mkstemp(dir=USER_CONFIG_DIR, prefix="config_", suffix=".tmp")
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        shutil.move(temp_path, USER_CONFIG_FILE)
        logger.info(f"Configuration successfully saved to {USER_CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}", exc_info=True)
        return False
