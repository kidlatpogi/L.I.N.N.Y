"""
Real-time Activity and Recognition Logs View.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ...core.logger import get_memory_log_handler

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant


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
        header_row.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header_row,
            text="📜 Live Activity & Console Logs",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        clear_btn = ctk.CTkButton(
            header_row,
            text="Clear Console",
            command=self._on_clear,
            width=110,
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=12),
        )
        clear_btn.pack(side="right")

        self.log_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#0f172a",
            text_color="#38bdf8",
            corner_radius=12,
        )
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))

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
