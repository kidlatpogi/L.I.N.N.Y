"""
App Aliases and Quick Launcher Management View.
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

import tkinter.filedialog as fd
from typing import TYPE_CHECKING, Any, Dict

import customtkinter as ctk

from ...core.config import save_config
from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.shortcuts")

COLOR_SURFACE = "#1A1A1A"
COLOR_SURFACE_ALT = "#242424"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


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
            text="Application Shortcuts and Aliases",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Map natural voice phrases (e.g. 'open valorant') to applications, games, custom scripts, or URLs.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=28, pady=(0, 16))

        # Add New Alias Card
        add_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        add_card.pack(fill="x", padx=28, pady=(0, 16))

        add_inner = ctk.CTkFrame(add_card, fg_color="transparent")
        add_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            add_inner,
            text="Add New Voice Shortcut:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 10))

        row1 = ctk.CTkFrame(add_inner, fg_color="transparent")
        row1.pack(fill="x")

        self.new_key_entry = ctk.CTkEntry(
            row1,
            placeholder_text="Voice Trigger (e.g. spotify, notes, valorant)",
            width=220,
            height=36,
            font=ctk.CTkFont(size=12),
            border_color=COLOR_BORDER,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.new_key_entry.pack(side="left", padx=(0, 10))

        self.new_val_entry = ctk.CTkEntry(
            row1,
            placeholder_text="Target file path, executable, or web URL",
            height=36,
            font=ctk.CTkFont(size=12),
            border_color=COLOR_BORDER,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.new_val_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            row1,
            text="Browse...",
            command=self._on_browse_file,
            width=85,
            height=36,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        browse_btn.pack(side="left", padx=(0, 8))

        add_btn = ctk.CTkButton(
            row1,
            text="Add Shortcut",
            command=self._on_add_alias,
            width=110,
            height=36,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        add_btn.pack(side="right")

        # Scrollable Aliases Table Frame
        self.table_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12,
        )
        self.table_frame.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        self._render_alias_rows()

    def _render_alias_rows(self) -> None:
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not self.aliases:
            ctk.CTkLabel(
                self.table_frame,
                text="No custom voice shortcuts configured yet.",
                text_color=COLOR_TEXT_SECONDARY,
            ).pack(pady=30)
            return

        # Header Row
        header_row = ctk.CTkFrame(self.table_frame, fg_color="#181818", height=32, corner_radius=6)
        header_row.pack(fill="x", padx=10, pady=(10, 6))
        ctk.CTkLabel(header_row, text="VOICE TRIGGER", width=150, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=12)
        ctk.CTkLabel(header_row, text="TARGET COMMAND / PATH", anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_PRIMARY).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(header_row, text="ACTIONS", width=130, anchor="center", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_PRIMARY).pack(side="right", padx=12)

        for key, target in sorted(self.aliases.items()):
            row = ctk.CTkFrame(self.table_frame, fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)

            ctk.CTkLabel(
                row,
                text=key,
                width=150,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLOR_TEXT_PRIMARY,
            ).pack(side="left", padx=12)

            ctk.CTkLabel(
                row,
                text=target,
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=COLOR_TEXT_SECONDARY,
            ).pack(side="left", fill="x", expand=True)

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=5)

            test_btn = ctk.CTkButton(
                btn_box,
                text="Launch",
                command=lambda k=key: self.assistant.launcher.launch(k),
                width=55,
                height=28,
                fg_color=COLOR_BTN_BG,
                hover_color=COLOR_BTN_HOVER,
                text_color=COLOR_TEXT_PRIMARY,
                border_color=COLOR_BORDER,
                border_width=1,
                font=ctk.CTkFont(size=11),
                corner_radius=4,
            )
            test_btn.pack(side="left", padx=3)

            del_btn = ctk.CTkButton(
                btn_box,
                text="Delete",
                command=lambda k=key: self._on_delete_alias(k),
                width=55,
                height=28,
                fg_color="#2A1B1B",
                hover_color="#4A1E1E",
                text_color="#E08080",
                border_color="#552222",
                border_width=1,
                font=ctk.CTkFont(size=11),
                corner_radius=4,
            )
            del_btn.pack(side="left", padx=3)

    def _on_browse_file(self) -> None:
        filename = fd.askopenfilename(
            title="Select Executable or Shortcut",
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
