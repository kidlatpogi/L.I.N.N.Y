"""
Main CustomTkinter Dashboard Window Shell for Linny.
Houses sidebar navigation, view switching, window lifecycle, and system tray integration.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Dict, Type

import customtkinter as ctk

from ..core.logger import get_logger
from .views.ai_view import AIView
from .views.calendar_view import CalendarView
from .views.logs_view import LogsView
from .views.overview_view import OverviewView
from .views.settings_view import SettingsView
from .views.shortcuts_view import ShortcutsView
from .views.smarthome_view import SmartHomeView

if TYPE_CHECKING:
    from ..core.assistant import LinnyAssistant

logger = get_logger("ui.app")


class LinnyAppWindow:
    """Master CustomTkinter application window with sidebar navigation."""

    def __init__(self, assistant: LinnyAssistant) -> None:
        self.assistant = assistant
        self.root: ctk.CTk | None = None
        self.current_view_name = "overview"
        self.views: Dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

    def initialize_gui(self) -> None:
        """Create and configure the root CustomTkinter window."""
        if self.root is not None:
            return

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("L.I.N.N.Y. - AI Assistant v1.1.0")
        self.root.geometry("1020x720")
        self.root.minsize(880, 600)

        # Configure 2-column layout (Sidebar + Content View)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Handle window close (minimize to system tray)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        logger.info("CustomTkinter GUI initialized")

    def _build_sidebar(self) -> None:
        assert self.root is not None
        sidebar = ctk.CTkFrame(self.root, width=220, corner_radius=0, fg_color="#0f172a")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)

        # Logo / Title
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=20, pady=(25, 20), sticky="w")

        ctk.CTkLabel(
            brand_frame,
            text="L.I.N.N.Y.",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#38bdf8",
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text="v1.1.0 • Neural Voice",
            font=ctk.CTkFont(size=11),
            text_color="#64748b",
        ).pack(anchor="w")

        # Navigation Items
        nav_items = [
            ("overview", "🏠  Overview", OverviewView),
            ("ai", "🧠  AI Assistants", AIView),
            ("smarthome", "💡  Smart Lighting", SmartHomeView),
            ("shortcuts", "🚀  App Shortcuts", ShortcutsView),
            ("calendar", "📅  Calendar", CalendarView),
            ("settings", "⚙️  Settings", SettingsView),
            ("logs", "📜  Activity Logs", LogsView),
        ]

        for idx, (key, title, view_cls) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=title,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color="#cbd5e1",
                hover_color="#1e293b",
                font=ctk.CTkFont(size=13, weight="normal"),
                command=lambda k=key: self.switch_view(k),
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        # Bottom Actions
        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.grid(row=9, column=0, padx=12, pady=15, sticky="ew")

        min_btn = ctk.CTkButton(
            bottom_frame,
            text="Minimize to Tray",
            command=self.hide,
            height=32,
            fg_color="#1e293b",
            hover_color="#334155",
            font=ctk.CTkFont(size=11),
        )
        min_btn.pack(fill="x", pady=(0, 6))

        exit_btn = ctk.CTkButton(
            bottom_frame,
            text="Exit Linny",
            command=self.exit_application,
            height=32,
            fg_color="#ef4444",
            hover_color="#dc2626",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        exit_btn.pack(fill="x")

    def _build_content_area(self) -> None:
        assert self.root is not None
        self.content_container = ctk.CTkFrame(self.root, fg_color="#0b1120", corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Initialize default view
        self.switch_view("overview")

    def switch_view(self, view_name: str) -> None:
        """Switch active dashboard view."""
        self.current_view_name = view_name

        # Update button highlights
        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(fg_color="#1e293b", text_color="#38bdf8", font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#cbd5e1", font=ctk.CTkFont(size=13, weight="normal"))

        # Create or raise view
        view_classes: Dict[str, Type[ctk.CTkFrame]] = {
            "overview": OverviewView,
            "ai": AIView,
            "smarthome": SmartHomeView,
            "shortcuts": ShortcutsView,
            "calendar": CalendarView,
            "settings": SettingsView,
            "logs": LogsView,
        }

        if view_name not in self.views and view_name in view_classes:
            view_cls = view_classes[view_name]
            instance = view_cls(self.content_container, self.assistant)
            instance.grid(row=0, column=0, sticky="nsew")
            self.views[view_name] = instance

        # Raise selected view
        if view_name in self.views:
            self.views[view_name].tkraise()

    def show(self) -> None:
        """Display the GUI window."""
        if self.root is None:
            self.initialize_gui()
        assert self.root is not None
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide(self) -> None:
        """Minimize window to background system tray."""
        if self.root is not None:
            self.root.withdraw()

    def toggle_visibility(self) -> None:
        if self.root is None:
            self.show()
        elif self.root.winfo_viewable():
            self.hide()
        else:
            self.show()

    def exit_application(self) -> None:
        """Gracefully shut down assistant and quit."""
        logger.info("Shutting down Linny...")
        self.assistant.stop()
        if self.root is not None:
            self.root.quit()
            self.root.destroy()
            self.root = None
        sys.exit(0)

    def mainloop(self) -> None:
        """Run the Tkinter event loop."""
        if self.root is None:
            self.initialize_gui()
        assert self.root is not None
        self.root.mainloop()
