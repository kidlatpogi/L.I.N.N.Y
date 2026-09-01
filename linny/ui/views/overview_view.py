"""
Overview Dashboard View for Linny Assistant.
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

from ...core.events import EventBus, EventType
from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.overview")

COLOR_BG = "#121212"
COLOR_SURFACE = "#1A1A1A"
COLOR_SURFACE_ALT = "#242424"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


class OverviewView(ctk.CTkFrame):
    """Primary dashboard overview view."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self.event_bus = EventBus()

        self._build_ui()
        self._subscribe_events()

    def _build_ui(self) -> None:
        # Title Section
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=28, pady=(24, 6))

        ctk.CTkLabel(
            title_row,
            text=f"Welcome, {self.assistant.config.user_name}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_row,
            text="Neural voice assistant is active and standing by.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(2, 0))

        # Status Card
        self.status_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12,
        )
        self.status_card.pack(fill="x", padx=28, pady=(12, 16))

        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=18)

        # Status badge indicator
        self.status_badge = ctk.CTkLabel(
            status_inner,
            text="LISTENING",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_SURFACE_ALT,
            corner_radius=6,
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side="left")

        self.status_desc = ctk.CTkLabel(
            status_inner,
            text="Microphone active. Say 'Hey Linny' or enter a voice command below.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.status_desc.pack(side="left", padx=16)

        # Control Buttons on Status Card
        btn_frame = ctk.CTkFrame(status_inner, fg_color="transparent")
        btn_frame.pack(side="right")

        self.mute_btn = ctk.CTkButton(
            btn_frame,
            text="Mute Mic",
            command=self._on_mute_click,
            width=95,
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.mute_btn.pack(side="left", padx=4)

        self.stop_speech_btn = ctk.CTkButton(
            btn_frame,
            text="Stop Speech",
            command=self._on_stop_speech_click,
            width=95,
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.stop_speech_btn.pack(side="left", padx=4)

        # Command Bar Card
        cmd_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12,
        )
        cmd_card.pack(fill="x", padx=28, pady=(0, 16))

        cmd_inner = ctk.CTkFrame(cmd_card, fg_color="transparent")
        cmd_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            cmd_inner,
            text="Command & Prompt Bar",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        input_row = ctk.CTkFrame(cmd_inner, fg_color="transparent")
        input_row.pack(fill="x")

        self.cmd_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Enter command (e.g. 'what is the weather', 'lights on', 'open spotify', 'who is Nikola Tesla')",
            height=40,
            corner_radius=6,
            border_color=COLOR_BORDER,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.cmd_entry.bind("<Return>", lambda e: self._on_send_command())

        send_btn = ctk.CTkButton(
            input_row,
            text="Send",
            command=self._on_send_command,
            width=85,
            height=40,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        send_btn.pack(side="right")

        # 3-Column Quick Widgets Grid
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="equal")

        # Card 1: Accurate Weather
        card1 = ctk.CTkFrame(grid_frame, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        card1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            card1,
            text="Live Weather",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.weather_city_label = ctk.CTkLabel(
            card1,
            text=f"Location: {self.assistant.config.weather_city}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_ACCENT,
        )
        self.weather_city_label.pack(anchor="w", padx=16, pady=(0, 4))

        self.weather_label = ctk.CTkLabel(
            card1,
            text="Fetching live weather forecast...",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=210,
            justify="left",
        )
        self.weather_label.pack(anchor="w", padx=16, pady=(0, 12))

        speak_weather_btn = ctk.CTkButton(
            card1,
            text="Speak Weather",
            command=lambda: self.assistant.execute_command("weather"),
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        speak_weather_btn.pack(fill="x", padx=16, pady=(0, 16))

        # Card 2: Smart Lighting
        card2 = ctk.CTkFrame(grid_frame, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        card2.grid(row=0, column=1, padx=5, sticky="nsew")

        ctk.CTkLabel(
            card2,
            text="Smart Lighting",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.bulb_status_label = ctk.CTkLabel(
            card2,
            text=f"Device: {self.assistant.config.smart_bulb_ip}\nStatus: Ready",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
        )
        self.bulb_status_label.pack(anchor="w", padx=16, pady=(0, 12))

        light_row = ctk.CTkFrame(card2, fg_color="transparent")
        light_row.pack(fill="x", padx=16, pady=(0, 16))

        on_btn = ctk.CTkButton(
            light_row,
            text="Turn ON",
            command=lambda: self.assistant.smart_home.turn_on(),
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        on_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        off_btn = ctk.CTkButton(
            light_row,
            text="Turn OFF",
            command=lambda: self.assistant.smart_home.turn_off(),
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        off_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 3: Neural Voice
        card3 = ctk.CTkFrame(grid_frame, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        card3.grid(row=0, column=2, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(
            card3,
            text="Voice Engine",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.voice_desc_label = ctk.CTkLabel(
            card3,
            text=f"Engine: Microsoft Neural\nVoice: {self.assistant.config.voice_en}",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
        )
        self.voice_desc_label.pack(anchor="w", padx=16, pady=(0, 12))

        greet_btn = ctk.CTkButton(
            card3,
            text="Test Greeting",
            command=lambda: self.assistant.run_startup_sequence(),
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        greet_btn.pack(fill="x", padx=16, pady=(0, 16))

        # Fetch weather in background non-blocking
        self.after(300, lambda: threading.Thread(target=self._update_weather_preview, daemon=True).start())

    def _subscribe_events(self) -> None:
        self.event_bus.subscribe(EventType.STATE_CHANGED, self._on_state_changed)
        self.event_bus.subscribe(EventType.MUTE_TOGGLED, self._on_mute_toggled)

    def _on_state_changed(self, payload: dict) -> None:
        state = payload.get("state", "listening")
        desc = payload.get("description", "Ready")

        def _update():
            if not self.winfo_exists():
                return
            state_styles = {
                "listening": ("LISTENING", COLOR_SURFACE_ALT),
                "speaking": ("SPEAKING", "#2E2E2E"),
                "processing": ("THINKING", "#383838"),
                "muted": ("MUTED", "#381818"),
                "error": ("ERROR", "#381818"),
                "idle": ("IDLE", COLOR_SURFACE_ALT),
            }
            badge_text, badge_color = state_styles.get(state, ("ACTIVE", COLOR_SURFACE_ALT))
            self.status_badge.configure(text=badge_text, fg_color=badge_color)
            self.status_desc.configure(text=desc)

        self.after(0, _update)

    def _on_mute_toggled(self, payload: dict) -> None:
        is_muted = payload.get("is_muted", False)

        def _update():
            if not self.winfo_exists():
                return
            if is_muted:
                self.mute_btn.configure(text="Unmute Mic", fg_color="#381818")
            else:
                self.mute_btn.configure(text="Mute Mic", fg_color=COLOR_BTN_BG)

        self.after(0, _update)

    def _on_mute_click(self) -> None:
        self.assistant.toggle_mute()

    def _on_stop_speech_click(self) -> None:
        self.assistant.voice.stop()

    def _on_send_command(self) -> None:
        cmd = self.cmd_entry.get().strip()
        if cmd:
            self.cmd_entry.delete(0, "end")
            threading.Thread(target=self.assistant.execute_command, args=(cmd,), daemon=True).start()

    def _update_weather_preview(self) -> None:
        try:
            data = self.assistant.weather.fetch_weather()
            temp = data.get("temperature")
            feels_like = data.get("feels_like", temp)
            cond = data.get("condition", "Clear")
            humidity = data.get("humidity", 70)

            if temp is not None:
                text = f"{temp} C (Feels like {feels_like} C)\n{cond} | Humidity: {humidity}%"
            else:
                text = "Weather currently offline"

            def _update():
                try:
                    if self.winfo_exists():
                        self.weather_label.configure(text=text)
                except Exception:
                    pass

            try:
                if self.winfo_exists():
                    self.after(0, _update)
            except Exception:
                pass
        except Exception:
            pass
