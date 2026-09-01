"""
General Settings, Voice Synthesis Engine, Profile, Location Geocoding, and Startup Configuration View.
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

from ...audio.tts import EDGE_VOICES
from ...core.config import save_config
from ...core.logger import get_logger
from ...system.startup import StartupManager

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.settings")

COLOR_SURFACE = "#1A1A1A"
COLOR_SURFACE_ALT = "#242424"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


class SettingsView(ctk.CTkScrollableFrame):
    """Configuration and preference controls."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Preferences and Voice Synthesis",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Customize personal preferences, speech synthesis, geocoding location, and Windows boot behavior.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=28, pady=(0, 16))

        # 1. Profile & Geocoding Card
        prof_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        prof_card.pack(fill="x", padx=28, pady=(0, 16))

        prof_inner = ctk.CTkFrame(prof_card, fg_color="transparent")
        prof_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(prof_inner, text="User Profile and Geolocation", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 12))

        # User Name
        row1 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        ctk.CTkLabel(row1, text="User Name:", width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.name_entry = ctk.CTkEntry(row1, height=34, font=ctk.CTkFont(size=12), border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_PRIMARY)
        self.name_entry.insert(0, self.assistant.config.user_name)
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Language
        row2 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        ctk.CTkLabel(row2, text="Assistant Language:", width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.lang_var = ctk.StringVar(value=self.assistant.config.language)
        lang_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.lang_var,
            values=["English", "Tagalog"],
            height=34,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            button_color=COLOR_BORDER,
            button_hover_color="#555555",
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_SURFACE_ALT,
        )
        lang_menu.pack(side="left", fill="x", expand=True)

        # City Geolocation
        row3 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row3.pack(fill="x", pady=4)
        ctk.CTkLabel(row3, text="Weather City / Area:", width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.city_entry = ctk.CTkEntry(row3, placeholder_text="e.g. Silang, Cavite or Manila", height=34, font=ctk.CTkFont(size=12), border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_PRIMARY)
        self.city_entry.insert(0, self.assistant.config.weather_city)
        self.city_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        geocode_btn = ctk.CTkButton(
            row3,
            text="Locate City",
            command=self._on_geocode_city,
            width=90,
            height=34,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        geocode_btn.pack(side="right")

        self.geocode_status = ctk.CTkLabel(prof_inner, text="", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SECONDARY)
        self.geocode_status.pack(anchor="w", padx=150, pady=(2, 4))

        # Timezone
        row4 = ctk.CTkFrame(prof_inner, fg_color="transparent")
        row4.pack(fill="x", pady=4)
        ctk.CTkLabel(row4, text="Timezone:", width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.tz_entry = ctk.CTkEntry(row4, height=34, font=ctk.CTkFont(size=12), border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_PRIMARY)
        self.tz_entry.insert(0, self.assistant.config.timezone)
        self.tz_entry.pack(side="left", fill="x", expand=True)

        # 2. Voice Engine Card
        voice_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        voice_card.pack(fill="x", padx=28, pady=(0, 16))

        voice_inner = ctk.CTkFrame(voice_card, fg_color="transparent")
        voice_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(voice_inner, text="Text-to-Speech (TTS) Voice Engine", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 12))

        # Neural Voice Selection
        vrow1 = ctk.CTkFrame(voice_inner, fg_color="transparent")
        vrow1.pack(fill="x", pady=4)
        ctk.CTkLabel(vrow1, text="Neural Voice:", width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")

        voice_display_names = list(EDGE_VOICES.keys())
        current_voice_display = voice_display_names[0]
        for name, vid in EDGE_VOICES.items():
            if vid == self.assistant.config.voice_en:
                current_voice_display = name
                break

        self.voice_var = ctk.StringVar(value=current_voice_display)
        voice_menu = ctk.CTkOptionMenu(
            vrow1,
            variable=self.voice_var,
            values=voice_display_names,
            height=34,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            button_color=COLOR_BORDER,
            button_hover_color="#555555",
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_SURFACE_ALT,
        )
        voice_menu.pack(side="left", fill="x", expand=True)

        # Volume Slider
        vrow2 = ctk.CTkFrame(voice_inner, fg_color="transparent")
        vrow2.pack(fill="x", pady=8)
        ctk.CTkLabel(vrow2, text="Master Volume:", width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.volume_slider = ctk.CTkSlider(
            vrow2,
            from_=0.1,
            to=1.0,
            number_of_steps=10,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_TEXT_PRIMARY,
            progress_color=COLOR_ACCENT,
        )
        self.volume_slider.set(self.assistant.config.tts_volume)
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        test_voice_btn = ctk.CTkButton(
            voice_inner,
            text="Preview Selected Voice",
            command=self._on_test_voice,
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        test_voice_btn.pack(fill="x", pady=(8, 0))

        # 3. Windows Startup & System Card
        sys_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        sys_card.pack(fill="x", padx=28, pady=(0, 20))

        sys_inner = ctk.CTkFrame(sys_card, fg_color="transparent")
        sys_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(sys_inner, text="Windows System and Startup", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 12))

        # Auto-Start switch
        is_autostart = StartupManager.is_startup_enabled()
        self.startup_switch = ctk.CTkSwitch(
            sys_inner,
            text="Start Linny automatically on Windows Boot",
            command=self._on_toggle_startup,
            font=ctk.CTkFont(size=12),
            progress_color=COLOR_ACCENT,
            button_color=COLOR_TEXT_PRIMARY,
        )
        if is_autostart:
            self.startup_switch.select()
        else:
            self.startup_switch.deselect()
        self.startup_switch.pack(anchor="w", pady=6)

        # Lock Workstation switch
        self.lock_switch = ctk.CTkSwitch(
            sys_inner,
            text="Lock PC workstation on startup sequence",
            font=ctk.CTkFont(size=12),
            progress_color=COLOR_ACCENT,
            button_color=COLOR_TEXT_PRIMARY,
        )
        if self.assistant.config.lock_on_startup:
            self.lock_switch.select()
        else:
            self.lock_switch.deselect()
        self.lock_switch.pack(anchor="w", pady=6)

        # Save Button Bar
        save_btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        save_btn_bar.pack(fill="x", padx=28, pady=(0, 24))

        save_btn = ctk.CTkButton(
            save_btn_bar,
            text="Save All Settings",
            command=self._on_save_all,
            width=160,
            height=38,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
        )
        save_btn.pack(side="left")

        self.save_status = ctk.CTkLabel(save_btn_bar, text="", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_SECONDARY)
        self.save_status.pack(side="left", padx=15)

    def _on_geocode_city(self) -> None:
        city = self.city_entry.get().strip()
        if not city:
            return
        self.geocode_status.configure(text="Locating city coordinates...", text_color=COLOR_TEXT_SECONDARY)

        def _worker():
            res = self.assistant.weather.geocode_city(city)

            def _update():
                if not self.winfo_exists():
                    return
                if res:
                    lat, lon, tz, name = res
                    self.assistant.config.weather_latitude = lat
                    self.assistant.config.weather_longitude = lon
                    self.assistant.config.weather_city = name
                    self.city_entry.delete(0, "end")
                    self.city_entry.insert(0, name)
                    self.tz_entry.delete(0, "end")
                    self.tz_entry.insert(0, tz)
                    self.geocode_status.configure(text=f"Located: {name} ({lat:.2f}, {lon:.2f})", text_color=COLOR_TEXT_PRIMARY)
                else:
                    self.geocode_status.configure(text=f"Could not find '{city}'.", text_color="#E08080")

            self.after(0, _update)

        threading.Thread(target=_worker, daemon=True).start()

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
        self.assistant.config.weather_city = self.city_entry.get().strip()

        selected_display = self.voice_var.get()
        self.assistant.config.voice_en = EDGE_VOICES.get(selected_display, "en-PH-RosaNeural")
        self.assistant.config.tts_volume = float(self.volume_slider.get())
        self.assistant.config.lock_on_startup = bool(self.lock_switch.get())

        save_config(self.assistant.config)
        self.assistant.reload_config(self.assistant.config)
        self.save_status.configure(text="All preferences saved and applied.")
