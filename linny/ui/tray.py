"""
System Tray Icon Manager for Linny using pystray.
Supports dynamic state colors (Green=Listening, Blue=Speaking, Red=Muted, Yellow=Processing)
and system context menu.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

from ..core.events import EventBus, EventType
from ..core.logger import get_logger

logger = get_logger("tray")


class SystemTrayManager:
    """Windows System Tray Icon coordinator with real-time status indicators."""

    def __init__(
        self,
        on_show_dashboard: Callable[[], None],
        on_toggle_mute: Callable[[], None],
        on_interrupt: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self.on_show_dashboard = on_show_dashboard
        self.on_toggle_mute = on_toggle_mute
        self.on_interrupt = on_interrupt
        self.on_exit = on_exit

        self.icon: Optional[pystray.Icon] = None
        self.current_state = "listening"
        self._event_bus = EventBus()
        self._event_bus.subscribe(EventType.STATE_CHANGED, self._on_state_event)
        self._event_bus.subscribe(EventType.MUTE_TOGGLED, self._on_mute_event)

    def _create_icon_image(self, color_name: str) -> Image.Image:
        """Draw an anti-aliased status icon."""
        width = 64
        height = 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        color_map = {
            "green": (46, 204, 113, 255),    # Ready / Listening
            "blue": (52, 152, 219, 255),     # Speaking
            "yellow": (241, 196, 15, 255),   # Processing
            "red": (231, 76, 60, 255),       # Muted
            "gray": (149, 165, 166, 255),    # Standby
        }
        fill_color = color_map.get(color_name, (46, 204, 113, 255))

        # Outer glowing ring
        draw.ellipse([6, 6, 58, 58], fill=(30, 30, 30, 200), outline=fill_color, width=3)
        # Inner core
        draw.ellipse([16, 16, 48, 48], fill=fill_color)
        return image

    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("Open Dashboard", lambda: self.on_show_dashboard(), default=True),
            pystray.MenuItem("Toggle Mute", lambda: self.on_toggle_mute()),
            pystray.MenuItem("Interrupt Speech", lambda: self.on_interrupt()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Linny", lambda: self.on_exit()),
        )

    def _on_state_event(self, payload: dict) -> None:
        state = payload.get("state", "listening")
        self.update_state(state)

    def _on_mute_event(self, payload: dict) -> None:
        is_muted = payload.get("is_muted", False)
        self.update_state("muted" if is_muted else "listening")

    def update_state(self, state: str) -> None:
        self.current_state = state
        if not self.icon:
            return

        state_color_map = {
            "listening": "green",
            "speaking": "blue",
            "processing": "yellow",
            "muted": "red",
            "error": "red",
            "idle": "gray",
        }
        color = state_color_map.get(state, "green")
        try:
            self.icon.icon = self._create_icon_image(color)
            self.icon.title = f"Linny ({state.capitalize()})"
        except Exception:
            pass

    def start(self) -> None:
        """Start the system tray icon in a dedicated daemon thread."""
        img = self._create_icon_image("green")
        self.icon = pystray.Icon(
            name="Linny",
            icon=img,
            title="Linny Voice Assistant",
            menu=self._create_menu(),
        )
        tray_thread = threading.Thread(target=self.icon.run, daemon=True, name="LinnyTrayWorker")
        tray_thread.start()
        logger.info("System Tray icon launched")

    def stop(self) -> None:
        if self.icon:
            self.icon.stop()
            self.icon = None
