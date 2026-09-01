"""
Windows Startup Manager and Process Priority Controller.
"""

from __future__ import annotations

import os
import sys
import winreg
from pathlib import Path
from typing import Optional

import psutil

from ..core.config import WORKSPACE_ROOT
from ..core.logger import get_logger

logger = get_logger("startup")

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "LinnyAssistant"


class StartupManager:
    """Manages Windows startup registry entry and process execution priority."""

    @staticmethod
    def set_high_priority() -> bool:
        """Elevate process priority for immediate wake word and hotkey responsiveness."""
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("Process priority elevated to HIGH")
            return True
        except Exception as e:
            logger.warning(f"Could not set process priority: {e}")
            return False

    @staticmethod
    def is_startup_enabled() -> bool:
        """Check if Linny is registered in Windows Startup registry."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"Error checking startup registry: {e}")
            return False

    @staticmethod
    def enable_startup(custom_command: Optional[str] = None) -> bool:
        """Register Linny in Windows HKCU Run registry."""
        try:
            if custom_command:
                command = custom_command
            else:
                python_exe = sys.executable
                pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
                exe_to_use = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
                command = f'"{exe_to_use}" -m linny.main --startup'

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            logger.info(f"Enabled Windows startup: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable Windows startup: {e}")
            return False

    @staticmethod
    def disable_startup() -> bool:
        """Remove Linny from Windows HKCU Run registry."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_NAME)
            logger.info("Disabled Windows startup registry entry")
            return True
        except FileNotFoundError:
            return True  # Already not registered
        except Exception as e:
            logger.error(f"Failed to disable Windows startup: {e}")
            return False
