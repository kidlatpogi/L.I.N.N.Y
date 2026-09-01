"""
Google Calendar and Schedule Preview View.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.calendar")


class CalendarView(ctk.CTkFrame):
    """Calendar integration and daily agenda viewer."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="📅 Google Calendar & Agenda",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Smart daily schedule filtering with upcoming event summaries and morning briefings.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Status & Connection Card
        card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        card.pack(fill="x", padx=20, pady=(0, 20))

        card_inner = ctk.CTkFrame(card, fg_color="transparent")
        card_inner.pack(fill="x", padx=20, pady=15)

        is_connected = self.assistant.calendar.is_connected()
        status_text = "● Google Calendar Connected" if is_connected else "○ Google Calendar Not Authenticated"
        status_color = "#22c55e" if is_connected else "#f59e0b"

        self.status_badge = ctk.CTkLabel(
            card_inner,
            text=status_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=status_color,
        )
        self.status_badge.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            card_inner,
            text=(
                "To connect Google Calendar, place your Google Cloud OAuth `credentials.json` in the Linny folder "
                "or click Sync to authorize your account."
            ),
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(0, 15))

        btn_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        sync_btn = ctk.CTkButton(
            btn_row,
            text="Refresh Schedule",
            command=self._on_refresh_schedule,
            width=140,
            height=36,
            fg_color="#06b6d4",
            hover_color="#0891b2",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        sync_btn.pack(side="left", padx=(0, 10))

        speak_btn = ctk.CTkButton(
            btn_row,
            text="Read Aloud",
            command=lambda: self.assistant.execute_command("schedule"),
            width=120,
            height=36,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=12),
        )
        speak_btn.pack(side="left")

        # Schedule Output Card
        sched_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        sched_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        sched_inner = ctk.CTkFrame(sched_card, fg_color="transparent")
        sched_inner.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            sched_inner,
            text="Upcoming Schedule Summary:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.schedule_text = ctk.CTkTextbox(
            sched_inner,
            font=ctk.CTkFont(size=13),
            fg_color="#0f172a",
            corner_radius=8,
        )
        self.schedule_text.pack(fill="both", expand=True)

        self._on_refresh_schedule()

    def _on_refresh_schedule(self) -> None:
        self.schedule_text.delete("0.0", "end")
        self.schedule_text.insert("0.0", "Querying calendar events...")

        def _worker():
            summary = self.assistant.calendar.get_schedule("")

            def _update():
                if self.winfo_exists():
                    self.schedule_text.delete("0.0", "end")
                    self.schedule_text.insert("0.0", summary)

            self.after(0, _update)

        threading.Thread(target=_worker, daemon=True).start()
