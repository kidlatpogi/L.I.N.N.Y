"""
Main CustomTkinter Dashboard Window Shell for Linny.
Strictly themed with:
- Background: #121212 (charcoal black)
- Primary Text: #E0E0E0 (light gray)
- Secondary Text: #B0B0B0 (medium gray)
- Borders/Dividers: #444444 (dark gray)
- Accent: #888888 (soft gray)
- Pre-instantiated views for 0ms instantaneous tab switching.
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

COLOR_BG = "#121212"
COLOR_SIDEBAR = "#0D0D0D"
COLOR_SURFACE = "#1A1A1A"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_HOVER = "#2D2D2D"


class LinnyAppWindow:
    """Master application window shell with instantaneous tab switching."""

    def __init__(self, assistant: LinnyAssistant) -> None:
        self.assistant = assistant
        self.root: ctk.CTk | None = None
        self.current_view_name = "overview"
        self.views: Dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

    def initialize_gui(self) -> None:
        """Create and configure the CustomTkinter dark-mode window."""
        if self.root is not None:
            return

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Linny Assistant")
        self.root.geometry("1060x740")
        self.root.minsize(920, 640)
        self.root.configure(fg_color=COLOR_BG)

        # 2-column layout (Sidebar + Content View)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Handle window close (minimize to system tray)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        logger.info("CustomTkinter GUI initialized with 0ms pre-instantiated views")

    def _build_sidebar(self) -> None:
        assert self.root is not None
        sidebar = ctk.CTkFrame(self.root, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)

        # Brand Header
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=22, pady=(28, 20), sticky="w")

        ctk.CTkLabel(
            brand_frame,
            text="LINNY",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text="VOICE ASSISTANT",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLOR_ACCENT,
        ).pack(anchor="w", pady=(2, 0))

        # Navigation Items (Clean icons on left sidebar only)
        nav_items = [
            ("overview", "Overview", OverviewView),
            ("ai", "AI Studio", AIView),
            ("smarthome", "Smart Lighting", SmartHomeView),
            ("shortcuts", "App Shortcuts", ShortcutsView),
            ("calendar", "Calendar", CalendarView),
            ("settings", "Preferences", SettingsView),
            ("logs", "Live Console", LogsView),
        ]

        for idx, (key, title, view_cls) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=title,
                anchor="w",
                height=40,
                corner_radius=6,
                fg_color="transparent",
                text_color=COLOR_TEXT_SECONDARY,
                hover_color=COLOR_BTN_HOVER,
                font=ctk.CTkFont(size=13, weight="normal"),
                command=lambda k=key: self.switch_view(k),
            )
            btn.grid(row=idx, column=0, padx=14, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        # Bottom Actions
        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.grid(row=9, column=0, padx=14, pady=20, sticky="ew")

        min_btn = ctk.CTkButton(
            bottom_frame,
            text="Minimize to Tray",
            command=self.hide,
            height=32,
            fg_color="#1E1E1E",
            hover_color="#2E2E2E",
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        min_btn.pack(fill="x", pady=(0, 6))

        exit_btn = ctk.CTkButton(
            bottom_frame,
            text="Exit",
            command=self.exit_application,
            height=32,
            fg_color="#2A1B1B",
            hover_color="#4A1E1E",
            text_color="#E08080",
            border_color="#552222",
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        exit_btn.pack(fill="x")

    def _build_content_area(self) -> None:
        assert self.root is not None
        self.content_container = ctk.CTkFrame(self.root, fg_color=COLOR_BG, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # PRE-INSTANTIATE ALL VIEWS IMMEDIATELY FOR ZERO-LAG TAB SWITCHING
        view_classes: Dict[str, Type[ctk.CTkFrame]] = {
            "overview": OverviewView,
            "ai": AIView,
            "smarthome": SmartHomeView,
            "shortcuts": ShortcutsView,
            "calendar": CalendarView,
            "settings": SettingsView,
            "logs": LogsView,
        }

        for key, view_cls in view_classes.items():
            instance = view_cls(self.content_container, self.assistant)
            instance.grid(row=0, column=0, sticky="nsew")
            self.views[key] = instance

        # Set default view
        self.switch_view("overview")

    def switch_view(self, view_name: str) -> None:
        """Instant 0ms tab switching using tkraise."""
        self.current_view_name = view_name

        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(
                    fg_color="#2A2A2A",
                    text_color=COLOR_TEXT_PRIMARY,
                    border_color=COLOR_BORDER,
                    border_width=1,
                    font=ctk.CTkFont(size=13, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXT_SECONDARY,
                    border_width=0,
                    font=ctk.CTkFont(size=13, weight="normal"),
                )

        if view_name in self.views:
            self.views[view_name].tkraise()

    def show(self) -> None:
        if self.root is None:
            self.initialize_gui()
        assert self.root is not None
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide(self) -> None:
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
        logger.info("Shutting down Linny...")
        self.assistant.stop()
        if self.root is not None:
            self.root.quit()
            self.root.destroy()
            self.root = None
        sys.exit(0)

    def mainloop(self) -> None:
        if self.root is None:
            self.initialize_gui()
        assert self.root is not None
        self.root.mainloop()
