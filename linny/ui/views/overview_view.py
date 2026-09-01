"""
Overview Dashboard View for Linny Assistant.
Features real-time assistant status, interactive command tester, quick toggles, and live system widgets.
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
        title_label = ctk.CTkLabel(
            self,
            text=f"Welcome back, {self.assistant.config.user_name} ✨",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(anchor="w", padx=25, pady=(20, 5))

        subtitle_label = ctk.CTkLabel(
            self,
            text="L.I.N.N.Y. Voice Assistant is standing by and active.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        )
        subtitle_label.pack(anchor="w", padx=25, pady=(0, 20))

        # Hero Status Card
        self.status_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        self.status_card.pack(fill="x", padx=25, pady=(0, 20))

        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=20)

        # Status badge indicator
        self.status_badge = ctk.CTkLabel(
            status_inner,
            text="● LISTENING",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#22c55e",
            fg_color="#0f172a",
            corner_radius=8,
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side="left")

        self.status_desc = ctk.CTkLabel(
            status_inner,
            text="Microphone active • Say 'Hey Linny' or type a command below",
            font=ctk.CTkFont(size=13),
            text_color="#cbd5e1",
        )
        self.status_desc.pack(side="left", padx=15)

        # Control Buttons on Status Card
        btn_frame = ctk.CTkFrame(status_inner, fg_color="transparent")
        btn_frame.pack(side="right")

        self.mute_btn = ctk.CTkButton(
            btn_frame,
            text="Mute Mic",
            command=self._on_mute_click,
            width=110,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.mute_btn.pack(side="left", padx=5)

        self.stop_speech_btn = ctk.CTkButton(
            btn_frame,
            text="Stop Speech",
            command=self._on_stop_speech_click,
            width=110,
            fg_color="#475569",
            hover_color="#334155",
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.stop_speech_btn.pack(side="left", padx=5)

        # Command Test Bar
        cmd_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        cmd_card.pack(fill="x", padx=25, pady=(0, 20))

        cmd_inner = ctk.CTkFrame(cmd_card, fg_color="transparent")
        cmd_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            cmd_inner,
            text="Execute Command / Ask Linny:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        input_row = ctk.CTkFrame(cmd_inner, fg_color="transparent")
        input_row.pack(fill="x")

        self.cmd_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Try: 'what is the weather', 'lights on', 'open spotify', 'who is Ada Lovelace'",
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.cmd_entry.bind("<Return>", lambda e: self._on_send_command())

        send_btn = ctk.CTkButton(
            input_row,
            text="Send",
            command=self._on_send_command,
            width=90,
            height=42,
            fg_color="#06b6d4",
            hover_color="#0891b2",
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        send_btn.pack(side="right")

        # Quick Actions Grid
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="equal")

        # Card 1: Time & Weather
        card1 = ctk.CTkFrame(grid_frame, fg_color="#1e293b", corner_radius=12)
        card1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            card1,
            text="🌤️ Weather & Location",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 8))

        self.weather_label = ctk.CTkLabel(
            card1,
            text="Fetching live weather forecast...",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            wraplength=190,
            justify="left",
        )
        self.weather_label.pack(anchor="w", padx=15, pady=(0, 15))

        test_weather_btn = ctk.CTkButton(
            card1,
            text="Speak Weather",
            command=lambda: self.assistant.execute_command("weather"),
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            corner_radius=6,
        )
        test_weather_btn.pack(fill="x", padx=15, pady=(0, 15))

        # Card 2: Smart Lighting
        card2 = ctk.CTkFrame(grid_frame, fg_color="#1e293b", corner_radius=12)
        card2.grid(row=0, column=1, padx=5, sticky="nsew")

        ctk.CTkLabel(
            card2,
            text="💡 Smart Lighting",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 8))

        self.bulb_status_label = ctk.CTkLabel(
            card2,
            text=f"Target IP: {self.assistant.config.smart_bulb_ip}\nStatus: Ready",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            justify="left",
        )
        self.bulb_status_label.pack(anchor="w", padx=15, pady=(0, 10))

        light_toggle_row = ctk.CTkFrame(card2, fg_color="transparent")
        light_toggle_row.pack(fill="x", padx=15, pady=(0, 15))

        on_btn = ctk.CTkButton(
            light_toggle_row,
            text="Turn ON",
            command=lambda: self.assistant.smart_home.turn_on(),
            fg_color="#10b981",
            hover_color="#059669",
            height=32,
            corner_radius=6,
        )
        on_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        off_btn = ctk.CTkButton(
            light_toggle_row,
            text="Turn OFF",
            command=lambda: self.assistant.smart_home.turn_off(),
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=32,
            corner_radius=6,
        )
        off_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Card 3: Voice & AI
        card3 = ctk.CTkFrame(grid_frame, fg_color="#1e293b", corner_radius=12)
        card3.grid(row=0, column=2, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(
            card3,
            text="🎙️ Voice Engine",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 8))

        self.voice_desc_label = ctk.CTkLabel(
            card3,
            text=f"Engine: Microsoft Neural\nVoice: {self.assistant.config.voice_en}",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            justify="left",
        )
        self.voice_desc_label.pack(anchor="w", padx=15, pady=(0, 10))

        greet_btn = ctk.CTkButton(
            card3,
            text="Test Greeting",
            command=lambda: self.assistant.run_startup_sequence(),
            height=32,
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            corner_radius=6,
        )
        greet_btn.pack(fill="x", padx=15, pady=(0, 15))

        # Fetch initial weather preview in background
        threading.Thread(target=self._update_weather_preview, daemon=True).start()

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
                "listening": ("● LISTENING", "#22c55e"),
                "speaking": ("● SPEAKING", "#3b82f6"),
                "processing": ("● THINKING", "#f59e0b"),
                "muted": ("● MUTED", "#ef4444"),
                "error": ("● ERROR", "#ef4444"),
                "idle": ("● IDLE", "#64748b"),
            }
            badge_text, badge_color = state_styles.get(state, ("● ACTIVE", "#22c55e"))
            self.status_badge.configure(text=badge_text, text_color=badge_color)
            self.status_desc.configure(text=desc)

        self.after(0, _update)

    def _on_mute_toggled(self, payload: dict) -> None:
        is_muted = payload.get("is_muted", False)

        def _update():
            if not self.winfo_exists():
                return
            if is_muted:
                self.mute_btn.configure(text="Unmute Mic", fg_color="#ef4444", hover_color="#dc2626")
            else:
                self.mute_btn.configure(text="Mute Mic", fg_color="#3b82f6", hover_color="#2563eb")

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
            temp, condition, _ = self.assistant.weather.fetch_weather()
            if temp is not None:
                text = f"Temperature: {round(temp)}°C\nCondition: {condition.capitalize()}\nZone: {self.assistant.config.timezone}"
            else:
                text = "Weather currently offline"

            def _update():
                if self.winfo_exists():
                    self.weather_label.configure(text=text)

            self.after(0, _update)
        except Exception:
            pass
