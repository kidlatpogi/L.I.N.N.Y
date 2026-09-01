"""
Google Calendar and Schedule Preview View.
Palette:
- Background: #121212 (charcoal black)
- Surface/Cards: #1A1A1A
- Primary Text: #E0E0E0 (light gray)
- Secondary Text: #B0B0B0 (medium gray)
- Borders/Dividers: #444444 (dark gray)
- Accent: #888888 (soft gray)
- Zero emojis inside view.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.calendar")

COLOR_SURFACE = "#1A1A1A"
COLOR_SURFACE_ALT = "#242424"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


class CalendarView(ctk.CTkFrame):
    """Calendar integration and daily agenda viewer."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Google Calendar and Agenda",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Daily schedule filtering with upcoming event summaries and morning briefings.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=28, pady=(0, 16))

        # Status & Connection Card
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="x", padx=28, pady=(0, 16))

        card_inner = ctk.CTkFrame(card, fg_color="transparent")
        card_inner.pack(fill="x", padx=20, pady=18)

        is_connected = self.assistant.calendar.is_connected()
        status_text = "Status: Google Calendar Connected" if is_connected else "Status: Google Calendar Not Authenticated"

        self.status_badge = ctk.CTkLabel(
            card_inner,
            text=status_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.status_badge.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            card_inner,
            text=(
                "To connect Google Calendar, place your Google Cloud OAuth credentials.json in the Linny root folder "
                "or click Refresh Schedule to pull updated events."
            ),
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        btn_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        sync_btn = ctk.CTkButton(
            btn_row,
            text="Refresh Schedule",
            command=self._on_refresh_schedule,
            width=140,
            height=34,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        sync_btn.pack(side="left", padx=(0, 8))

        speak_btn = ctk.CTkButton(
            btn_row,
            text="Read Aloud",
            command=lambda: self.assistant.execute_command("schedule"),
            width=110,
            height=34,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        speak_btn.pack(side="left")

        # Schedule Output Card
        sched_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        sched_card.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        sched_inner = ctk.CTkFrame(sched_card, fg_color="transparent")
        sched_inner.pack(fill="both", expand=True, padx=20, pady=18)

        ctk.CTkLabel(
            sched_inner,
            text="Upcoming Schedule Summary:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 10))

        self.schedule_text = ctk.CTkTextbox(
            sched_inner,
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.schedule_text.pack(fill="both", expand=True)

        self.after(300, self._on_refresh_schedule)

    def _on_refresh_schedule(self) -> None:
        if not self.winfo_exists():
            return
        self.schedule_text.delete("0.0", "end")
        self.schedule_text.insert("0.0", "Querying calendar events...")

        def _worker():
            summary = self.assistant.calendar.get_schedule("")

            def _update():
                try:
                    if self.winfo_exists():
                        self.schedule_text.delete("0.0", "end")
                        self.schedule_text.insert("0.0", summary)
                except Exception:
                    pass

            try:
                if self.winfo_exists():
                    self.after(0, _update)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()
