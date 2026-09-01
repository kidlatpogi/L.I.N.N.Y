"""
System power management, screen capture, media controls, and Windows OS operations.
"""

from __future__ import annotations

import ctypes
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pyautogui

from ..core.logger import get_logger

logger = get_logger("power")


class SystemPowerManager:
    """Windows OS operations: power states, screen capture, and media hotkeys."""

    def __init__(self, screenshot_dir: Optional[str] = None) -> None:
        if screenshot_dir:
            self.screenshot_dir = Path(screenshot_dir)
        else:
            self.screenshot_dir = Path.home() / "Pictures" / "Screenshots"

    def lock_workstation(self) -> bool:
        """Lock the Windows workstation."""
        try:
            logger.info("Executing LockWorkStation")
            ctypes.windll.user32.LockWorkStation()
            return True
        except Exception as e:
            logger.error(f"Failed to lock workstation: {e}")
            return False

    def shutdown(self, delay_seconds: int = 3) -> None:
        """Initiate Windows system shutdown with delay."""
        logger.info(f"System shutdown scheduled in {delay_seconds}s")
        threading.Timer(delay_seconds, lambda: os.system(f"shutdown /s /t 0")).start()

    def restart(self, delay_seconds: int = 3) -> None:
        """Initiate Windows system restart with delay."""
        logger.info(f"System restart scheduled in {delay_seconds}s")
        threading.Timer(delay_seconds, lambda: os.system(f"shutdown /r /t 0")).start()

    def sleep(self, delay_seconds: int = 1) -> None:
        """Put Windows PC into sleep / suspend mode."""
        logger.info(f"System sleep scheduled in {delay_seconds}s")
        threading.Timer(
            delay_seconds,
            lambda: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"),
        ).start()

    def take_screenshot(self) -> Tuple[bool, Optional[str]]:
        """Capture full screen and save to screenshot folder."""
        try:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = self.screenshot_dir / f"Screenshot_{timestamp}.png"
            pyautogui.screenshot(str(file_path))
            logger.info(f"Screenshot saved to: {file_path}")
            return True, str(file_path)
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return False, None

    def trigger_clip(self) -> bool:
        """Trigger instant replay clip via Alt+F10."""
        try:
            logger.info("Triggering GeForce/Xbox replay clip (Alt+F10)")
            pyautogui.hotkey("alt", "f10")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger clip: {e}")
            return False

    # Media Hotkey Emulation
    def media_play_pause(self) -> None:
        pyautogui.press("playpause")

    def media_next(self) -> None:
        pyautogui.press("nexttrack")

    def media_prev(self) -> None:
        pyautogui.press("prevtrack")

    def media_volume_up(self, steps: int = 2) -> None:
        for _ in range(steps):
            pyautogui.press("volumeup")

    def media_volume_down(self, steps: int = 2) -> None:
        for _ in range(steps):
            pyautogui.press("volumedown")

    def media_mute(self) -> None:
        pyautogui.press("volumemute")
