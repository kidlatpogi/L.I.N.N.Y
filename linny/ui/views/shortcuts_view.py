"""
App Aliases and Quick Launcher Management View.
Allows adding, modifying, testing, and deleting custom voice trigger shortcuts with file browser support.
"""

from __future__ import annotations

import tkinter.filedialog as fd
from typing import TYPE_CHECKING, Any, Dict

import customtkinter as ctk

from ...core.config import save_config
from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.shortcuts")


class ShortcutsView(ctk.CTkFrame):
    """Interactive in-app alias table and launcher editor."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self.aliases: Dict[str, str] = dict(self.assistant.config.app_aliases)
        self._build_ui()

    def _build_ui(self) -> None:
        # Title
        ctk.CTkLabel(
            self,
            text="🚀 Application Shortcuts & Aliases",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Map voice trigger phrases (e.g. 'open valorant') to local executables, games, protocols, or URLs.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # Add New Alias Card
        add_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        add_card.pack(fill="x", padx=20, pady=(0, 15))

        add_inner = ctk.CTkFrame(add_card, fg_color="transparent")
        add_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            add_inner,
            text="Add New Voice Shortcut:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        row1 = ctk.CTkFrame(add_inner, fg_color="transparent")
        row1.pack(fill="x")

        self.new_key_entry = ctk.CTkEntry(
            row1,
            placeholder_text="Trigger Name (e.g. spotify, valorant, notes)",
            width=200,
            font=ctk.CTkFont(size=12),
        )
        self.new_key_entry.pack(side="left", padx=(0, 10))

        self.new_val_entry = ctk.CTkEntry(
            row1,
            placeholder_text="Target path, URL, or command",
            font=ctk.CTkFont(size=12),
        )
        self.new_val_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            row1,
            text="Browse...",
            command=self._on_browse_file,
            width=80,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=12),
        )
        browse_btn.pack(side="left", padx=(0, 8))

        add_btn = ctk.CTkButton(
            row1,
            text="+ Add Alias",
            command=self._on_add_alias,
            width=90,
            fg_color="#06b6d4",
            hover_color="#0891b2",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        add_btn.pack(side="right")

        # Scrollable Aliases Table Frame
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#1e293b", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self._render_alias_rows()

    def _render_alias_rows(self) -> None:
        # Clear existing rows
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not self.aliases:
            ctk.CTkLabel(
                self.table_frame,
                text="No custom aliases defined yet.",
                text_color="#94a3b8",
            ).pack(pady=20)
            return

        # Header
        header_row = ctk.CTkFrame(self.table_frame, fg_color="#0f172a", height=32, corner_radius=6)
        header_row.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(header_row, text="VOICE TRIGGER", width=140, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(side="left", padx=10)
        ctk.CTkLabel(header_row, text="TARGET COMMAND / PATH", anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(header_row, text="ACTIONS", width=120, anchor="center", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(side="right", padx=10)

        for key, target in sorted(self.aliases.items()):
            row = ctk.CTkFrame(self.table_frame, fg_color="#334155", corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)

            # Trigger name
            ctk.CTkLabel(
                row,
                text=key,
                width=140,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#38bdf8",
            ).pack(side="left", padx=10)

            # Target path
            ctk.CTkLabel(
                row,
                text=target,
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color="#e2e8f0",
            ).pack(side="left", fill="x", expand=True)

            # Action Buttons
            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=4)

            test_btn = ctk.CTkButton(
                btn_box,
                text="Launch",
                command=lambda k=key: self.assistant.launcher.launch(k),
                width=55,
                height=26,
                fg_color="#10b981",
                hover_color="#059669",
                font=ctk.CTkFont(size=11),
            )
            test_btn.pack(side="left", padx=3)

            del_btn = ctk.CTkButton(
                btn_box,
                text="Delete",
                command=lambda k=key: self._on_delete_alias(k),
                width=55,
                height=26,
                fg_color="#ef4444",
                hover_color="#dc2626",
                font=ctk.CTkFont(size=11),
            )
            del_btn.pack(side="left", padx=3)

    def _on_browse_file(self) -> None:
        filename = fd.askopenfilename(
            title="Select Application or Game Executable",
            filetypes=[("Executables & Shortcuts", "*.exe *.bat *.cmd *.lnk *.url"), ("All Files", "*.*")],
        )
        if filename:
            self.new_val_entry.delete(0, "end")
            self.new_val_entry.insert(0, filename)

    def _on_add_alias(self) -> None:
        k = self.new_key_entry.get().strip().lower()
        v = self.new_val_entry.get().strip()
        if k and v:
            self.aliases[k] = v
            self.assistant.config.app_aliases = dict(self.aliases)
            save_config(self.assistant.config)
            self.assistant.launcher.update_aliases(self.aliases)

            self.new_key_entry.delete(0, "end")
            self.new_val_entry.delete(0, "end")
            self._render_alias_rows()

    def _on_delete_alias(self, key: str) -> None:
        if key in self.aliases:
            del self.aliases[key]
            self.assistant.config.app_aliases = dict(self.aliases)
            save_config(self.assistant.config)
            self.assistant.launcher.update_aliases(self.aliases)
            self._render_alias_rows()
