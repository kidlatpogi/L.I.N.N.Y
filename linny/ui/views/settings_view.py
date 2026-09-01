"""
General Settings, Voice Synthesis Engine, Profile, and Startup Configuration View.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ...audio.tts import EDGE_VOICES
from ...core.config import save_config
from ...core.logger import get_logger
from ...system.startup import StartupManager

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.settings")


class SettingsView(ctk.CTkScrollableFrame):
    """Configuration and preference controls."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="⚙️ Preferences & Voice Synthesis",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Customize personal preferences, speech voices, hotkeys, and Windows boot behavior.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Profile Card
        prof_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        prof_card.pack(fill="x", padx=20, pady=(0, 15))

        prof_inner = ctk.CTkFrame(prof_card, fg_color="transparent")
        prof_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(prof_inner, text="User Profile & Localization", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 10))

        # User Name
        row1 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        ctk.CTkLabel(row1, text="Your Name:", width=140, anchor="w").pack(side="left")
        self.name_entry = ctk.CTkEntry(row1, font=ctk.CTkFont(size=12))
        self.name_entry.insert(0, self.assistant.config.user_name)
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Language
        row2 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        ctk.CTkLabel(row2, text="Assistant Language:", width=140, anchor="w").pack(side="left")
        self.lang_var = ctk.StringVar(value=self.assistant.config.language)
        lang_menu = ctk.CTkOptionMenu(row2, variable=self.lang_var, values=["English", "Tagalog"])
        lang_menu.pack(side="left", fill="x", expand=True)

        # Timezone
        row3 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row3.pack(fill="x", pady=4)
        ctk.CTkLabel(row3, text="Timezone:", width=140, anchor="w").pack(side="left")
        self.tz_entry = ctk.CTkEntry(row3, font=ctk.CTkFont(size=12))
        self.tz_entry.insert(0, self.assistant.config.timezone)
        self.tz_entry.pack(side="left", fill="x", expand=True)

        # Voice Engine Card
        voice_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        voice_card.pack(fill="x", padx=20, pady=(0, 15))

        voice_inner = ctk.CTkFrame(voice_card, fg_color="transparent")
        voice_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(voice_inner, text="Text-to-Speech (TTS) Voice Engine", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 10))

        # Neural Voice Selection
        vrow1 = ctk.CTkFrame(voice_inner, fg_color="transparent")
        vrow1.pack(fill="x", pady=4)
        ctk.CTkLabel(vrow1, text="Edge Neural Voice:", width=140, anchor="w").pack(side="left")

        # Map display names to voice IDs
        voice_display_names = list(EDGE_VOICES.keys())
        current_voice_display = voice_display_names[0]
        for name, vid in EDGE_VOICES.items():
            if vid == self.assistant.config.voice_en:
                current_voice_display = name
                break

        self.voice_var = ctk.StringVar(value=current_voice_display)
        voice_menu = ctk.CTkOptionMenu(vrow1, variable=self.voice_var, values=voice_display_names)
        voice_menu.pack(side="left", fill="x", expand=True)

        # Volume Slider
        vrow2 = ctk.CTkFrame(voice_inner, fg_color="transparent")
        vrow2.pack(fill="x", pady=8)
        ctk.CTkLabel(vrow2, text="Master Volume:", width=140, anchor="w").pack(side="left")
        self.volume_slider = ctk.CTkSlider(vrow2, from_=0.1, to=1.0, number_of_steps=10)
        self.volume_slider.set(self.assistant.config.tts_volume)
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        test_voice_btn = ctk.CTkButton(
            voice_inner,
            text="Preview Selected Voice",
            command=self._on_test_voice,
            height=34,
            fg_color="#334155",
            hover_color="#475569",
        )
        test_voice_btn.pack(fill="x", pady=(8, 0))

        # Windows Startup & System Card
        sys_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        sys_card.pack(fill="x", padx=20, pady=(0, 20))

        sys_inner = ctk.CTkFrame(sys_card, fg_color="transparent")
        sys_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(sys_inner, text="Windows System & Startup", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 10))

        # Auto-Start switch
        is_autostart = StartupManager.is_startup_enabled()
        self.startup_switch = ctk.CTkSwitch(
            sys_inner,
            text="Start Linny automatically on Windows Boot",
            command=self._on_toggle_startup,
            font=ctk.CTkFont(size=13),
        )
        if is_autostart:
            self.startup_switch.select()
        else:
            self.startup_switch.deselect()
        self.startup_switch.pack(anchor="w", pady=6)

        # Lock Workstation switch
        self.lock_switch = ctk.CTkSwitch(
            sys_inner,
            text="Lock PC workstation automatically on startup sequence",
            font=ctk.CTkFont(size=13),
        )
        if self.assistant.config.lock_on_startup:
            self.lock_switch.select()
        else:
            self.lock_switch.deselect()
        self.lock_switch.pack(anchor="w", pady=6)

        # Save Button
        save_btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        save_btn_bar.pack(fill="x", padx=20, pady=(0, 20))

        save_btn = ctk.CTkButton(
            save_btn_bar,
            text="Save All Settings",
            command=self._on_save_all,
            width=160,
            height=42,
            fg_color="#06b6d4",
            hover_color="#0891b2",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        save_btn.pack(side="left")

        self.save_status = ctk.CTkLabel(save_btn_bar, text="", font=ctk.CTkFont(size=13), text_color="#22c55e")
        self.save_status.pack(side="left", padx=15)

    def _on_test_voice(self) -> None:
        selected_display = self.voice_var.get()
        voice_id = EDGE_VOICES.get(selected_display, "en-PH-RosaNeural")
        self.assistant.voice.set_voice(voice_id)
        self.assistant.voice.speak(f"Hello {self.name_entry.get().strip() or 'there'}, I am Linny with the {selected_display} voice.")

    def _on_toggle_startup(self) -> None:
        if self.startup_switch.get():
            StartupManager.enable_startup()
        else:
            StartupManager.disable_startup()

    def _on_save_all(self) -> None:
        self.assistant.config.user_name = self.name_entry.get().strip()
        self.assistant.config.language = self.lang_var.get()
        self.assistant.config.timezone = self.tz_entry.get().strip()

        selected_display = self.voice_var.get()
        self.assistant.config.voice_en = EDGE_VOICES.get(selected_display, "en-PH-RosaNeural")
        self.assistant.config.tts_volume = float(self.volume_slider.get())
        self.assistant.config.lock_on_startup = bool(self.lock_switch.get())

        save_config(self.assistant.config)
        self.assistant.reload_config(self.assistant.config)
        self.save_status.configure(text="✓ All settings saved and applied!")
