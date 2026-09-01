"""CustomTkinter dashboard tab views."""

from .ai_view import AIView
from .calendar_view import CalendarView
from .logs_view import LogsView
from .overview_view import OverviewView
from .settings_view import SettingsView
from .shortcuts_view import ShortcutsView
from .smarthome_view import SmartHomeView

__all__ = [
    "OverviewView",
    "AIView",
    "SmartHomeView",
    "ShortcutsView",
    "CalendarView",
    "SettingsView",
    "LogsView",
]
