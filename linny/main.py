"""
Main entry point for L.I.N.N.Y. Voice Assistant.
Usage:
    python -m linny.main            # Full GUI Dashboard Mode
    python -m linny.main --startup  # Windows Boot Mode (Tray + Greeting)
    python -m linny.main --headless # Background Tray-only Mode
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
import time

from .core.assistant import LinnyAssistant
from .core.config import load_config
from .core.logger import get_logger, setup_logging
from .ui.app import LinnyAppWindow
from .ui.tray import SystemTrayManager

logger = get_logger("main")


def set_process_metadata() -> None:
    """Configure Windows Task Manager title and console name."""
    try:
        ctypes.windll.kernel32.SetConsoleTitleW("Linny Voice Assistant")
        try:
            import setproctitle
            setproctitle.setproctitle("Linny")
        except ImportError:
            pass
    except Exception as e:
        logger.debug(f"Could not set process metadata: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="L.I.N.N.Y. Voice Assistant")
    parser.add_argument("--startup", action="store_true", help="Launch in Windows startup background mode")
    parser.add_argument("--headless", action="store_true", help="Run without opening GUI window")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    import logging
    setup_logging(level=logging.DEBUG if args.debug else logging.INFO)
    set_process_metadata()

    logger.info("Initializing Linny Assistant (v1.1.0)...")

    # Load configuration
    config = load_config()

    # Create Core Assistant
    assistant = LinnyAssistant(config)

    # Create UI Window
    window = LinnyAppWindow(assistant)

    # Create System Tray Manager
    tray = SystemTrayManager(
        on_show_dashboard=window.show,
        on_toggle_mute=assistant.toggle_mute,
        on_interrupt=assistant.voice.stop,
        on_exit=window.exit_application,
    )
    tray.start()

    # Register Global Hotkey
    try:
        import keyboard

        def _hotkey_action():
            logger.info("Global hotkey triggered -> Interrupt speech & toggle mute")
            assistant.voice.stop()
            assistant.toggle_mute()

        keyboard.add_hotkey(config.hotkey, _hotkey_action)
        logger.info(f"Global hotkey registered: {config.hotkey.upper()}")
    except Exception as e:
        logger.warning(f"Could not register global hotkey: {e}")

    # Launch behavior
    if args.startup:
        logger.info("Startup flag detected -> Running background sequence")
        assistant.run_startup_sequence()
        # Initialize GUI in background so it can be summoned instantly from tray
        window.initialize_gui()
        window.hide()
        window.mainloop()
    elif args.headless:
        logger.info("Headless flag detected -> Running in background tray mode")
        assistant.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            window.exit_application()
    else:
        # Standard desktop launch
        assistant.start()
        window.show()
        window.mainloop()


if __name__ == "__main__":
    main()
