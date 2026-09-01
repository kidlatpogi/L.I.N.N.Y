"""
Real-time Activity and Recognition Logs Console View.
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

from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ...core.logger import get_memory_log_handler

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

COLOR_SURFACE = "#1A1A1A"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_BORDER = "#444444"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


class LogsView(ctk.CTkFrame):
    """Live console displaying assistant activity and recognition logs."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self.log_handler = get_memory_log_handler()
        self._build_ui()
        self._attach_logger()

    def _build_ui(self) -> None:
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", padx=28, pady=(24, 10))

        ctk.CTkLabel(
            header_row,
            text="Live Activity and Console Logs",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        clear_btn = ctk.CTkButton(
            header_row,
            text="Clear Console",
            command=self._on_clear,
            width=110,
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        clear_btn.pack(side="right")

        console_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        console_card.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        self.log_box = ctk.CTkTextbox(
            console_card,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#101010",
            text_color="#D0D0D0",
            corner_radius=8,
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=12)

        # Populate initial logs
        initial_logs = self.log_handler.get_recent_logs()
        if initial_logs:
            self.log_box.insert("end", "\n".join(initial_logs) + "\n")
            self.log_box.see("end")

    def _attach_logger(self) -> None:
        self.log_handler.add_callback(self._on_new_log)

    def _on_new_log(self, log_msg: str) -> None:
        def _append():
            if not self.winfo_exists():
                return
            self.log_box.insert("end", log_msg + "\n")
            self.log_box.see("end")

        self.after(0, _append)

    def _on_clear(self) -> None:
        self.log_box.delete("0.0", "end")
