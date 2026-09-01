"""
Thread-safe Event Bus for publishing and subscribing to Linny lifecycle events.
Decouples UI, Audio, Core Assistant, and Integrations.
"""

from __future__ import annotations

import enum
import threading
from typing import Any, Callable, Dict, List


class EventType(str, enum.Enum):
    STATE_CHANGED = "state_changed"          # payload: {"state": str, "description": str}
    COMMAND_DETECTED = "command_detected"    # payload: {"query": str, "source": str}
    SPEECH_STARTED = "speech_started"        # payload: {"text": str}
    SPEECH_FINISHED = "speech_finished"      # payload: {}
    MUTE_TOGGLED = "mute_toggled"            # payload: {"is_muted": bool}
    SMART_HOME_UPDATE = "smart_home_update"  # payload: {"state": str, "info": Any}
    SETTINGS_SAVED = "settings_saved"        # payload: {"config": dict}
    SYSTEM_ALERT = "system_alert"            # payload: {"level": str, "message": str}


class EventBus:
    """Thread-safe event dispatcher."""

    _instance: EventBus | None = None
    _lock = threading.Lock()

    def __new__(cls) -> EventBus:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._subscribers = {}
                cls._instance._bus_lock = threading.RLock()
            return cls._instance

    def subscribe(self, event_type: EventType | str, callback: Callable[[Dict[str, Any]], None]) -> None:
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        with self._bus_lock:
            if key not in self._subscribers:
                self._subscribers[key] = []
            if callback not in self._subscribers[key]:
                self._subscribers[key].append(callback)

    def unsubscribe(self, event_type: EventType | str, callback: Callable[[Dict[str, Any]], None]) -> None:
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        with self._bus_lock:
            if key in self._subscribers and callback in self._subscribers[key]:
                self._subscribers[key].remove(callback)

    def publish(self, event_type: EventType | str, payload: Dict[str, Any] | None = None) -> None:
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        data = payload or {}
        with self._bus_lock:
            callbacks = list(self._subscribers.get(key, []))

        for cb in callbacks:
            try:
                cb(data)
            except Exception:
                # Do not let subscriber failures crash the event bus
                pass
