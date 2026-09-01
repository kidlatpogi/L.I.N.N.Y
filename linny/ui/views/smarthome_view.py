"""
Smart Home Management View for Tapo L530E and TP-Link Kasa Devices.
Supports device configuration, credentials, status diagnostics, and interactive controls.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from ...core.config import save_config
from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.smarthome")


class SmartHomeView(ctk.CTkScrollableFrame):
    """Smart home configuration and live controls view."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        ctk.CTkLabel(
            self,
            text="💡 Smart Lighting (Tapo L530E & Kasa)",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Control smart bulbs and plugs with high-performance local network automation.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Device Settings Card
        config_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        config_card.pack(fill="x", padx=20, pady=(0, 20))

        config_inner = ctk.CTkFrame(config_card, fg_color="transparent")
        config_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            config_inner,
            text="Device Network & Authentication",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        # Bulb IP
        ip_row = ctk.CTkFrame(config_inner, fg_color="transparent")
        ip_row.pack(fill="x", pady=4)
        ctk.CTkLabel(ip_row, text="Smart Bulb IP Address:", width=170, anchor="w").pack(side="left")
        self.ip_entry = ctk.CTkEntry(ip_row, placeholder_text="192.168.1.100", font=ctk.CTkFont(size=12))
        self.ip_entry.insert(0, self.assistant.config.smart_bulb_ip)
        self.ip_entry.pack(side="left", fill="x", expand=True)

        # Tapo Email
        email_row = ctk.CTkFrame(config_inner, fg_color="transparent")
        email_row.pack(fill="x", pady=4)
        ctk.CTkLabel(email_row, text="Tapo Email (Username):", width=170, anchor="w").pack(side="left")
        self.email_entry = ctk.CTkEntry(email_row, placeholder_text="your_email@example.com", font=ctk.CTkFont(size=12))
        self.email_entry.insert(0, self.assistant.config.tapo_email)
        self.email_entry.pack(side="left", fill="x", expand=True)

        # Tapo Password
        pass_row = ctk.CTkFrame(config_inner, fg_color="transparent")
        pass_row.pack(fill="x", pady=4)
        ctk.CTkLabel(pass_row, text="Tapo Cloud Password:", width=170, anchor="w").pack(side="left")
        self.pass_entry = ctk.CTkEntry(pass_row, placeholder_text="Password", show="*", font=ctk.CTkFont(size=12))
        self.pass_entry.insert(0, self.assistant.config.tapo_password)
        self.pass_entry.pack(side="left", fill="x", expand=True)

        # Save Button
        save_row = ctk.CTkFrame(config_inner, fg_color="transparent")
        save_row.pack(fill="x", pady=(10, 0))

        save_btn = ctk.CTkButton(
            save_row,
            text="Save & Connect",
            command=self._on_save_device,
            width=140,
            height=36,
            fg_color="#06b6d4",
            hover_color="#0891b2",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        save_btn.pack(side="left")

        self.save_status = ctk.CTkLabel(save_row, text="", font=ctk.CTkFont(size=12), text_color="#22c55e")
        self.save_status.pack(side="left", padx=10)

        # Interactive Controls Card
        control_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        control_card.pack(fill="x", padx=20, pady=(0, 20))

        control_inner = ctk.CTkFrame(control_card, fg_color="transparent")
        control_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            control_inner,
            text="Live Bulb Controls",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        # On / Off buttons
        power_row = ctk.CTkFrame(control_inner, fg_color="transparent")
        power_row.pack(fill="x", pady=(0, 15))

        on_btn = ctk.CTkButton(
            power_row,
            text="Turn ON",
            command=lambda: self.assistant.smart_home.turn_on(),
            fg_color="#10b981",
            hover_color="#059669",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        on_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        off_btn = ctk.CTkButton(
            power_row,
            text="Turn OFF",
            command=lambda: self.assistant.smart_home.turn_off(),
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        off_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Brightness Slider
        ctk.CTkLabel(control_inner, text="Brightness:").pack(anchor="w", pady=(5, 2))
        slider_row = ctk.CTkFrame(control_inner, fg_color="transparent")
        slider_row.pack(fill="x", pady=(0, 15))

        self.brightness_slider = ctk.CTkSlider(
            slider_row,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self._on_slider_change,
        )
        self.brightness_slider.set(100)
        self.brightness_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.brightness_val_label = ctk.CTkLabel(slider_row, text="100%", width=45)
        self.brightness_val_label.pack(side="right")

        # Lighting Preset Modes
        ctk.CTkLabel(control_inner, text="Lighting Modes:").pack(anchor="w", pady=(5, 5))
        mode_row = ctk.CTkFrame(control_inner, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 15))
        mode_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        modes = [
            ("Focus", "#3b82f6"),
            ("Movie", "#f59e0b"),
            ("Gaming", "#8b5cf6"),
            ("Night", "#64748b"),
            ("Relax", "#ec4899"),
        ]
        for idx, (m_name, color) in enumerate(modes):
            btn = ctk.CTkButton(
                mode_row,
                text=m_name,
                fg_color=color,
                command=lambda m=m_name: self.assistant.smart_home.set_mode(m),
                height=34,
            )
            btn.grid(row=0, column=idx, padx=3, sticky="nsew")

        # Color Buttons
        ctk.CTkLabel(control_inner, text="Color Swatches:").pack(anchor="w", pady=(5, 5))
        color_row = ctk.CTkFrame(control_inner, fg_color="transparent")
        color_row.pack(fill="x", pady=(0, 5))
        color_row.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        colors = [
            ("Red", "#ef4444"),
            ("Blue", "#3b82f6"),
            ("Green", "#22c55e"),
            ("Cyan", "#06b6d4"),
            ("Violet", "#8b5cf6"),
            ("Warm", "#f59e0b"),
        ]
        for idx, (c_name, hex_code) in enumerate(colors):
            btn = ctk.CTkButton(
                color_row,
                text=c_name,
                fg_color=hex_code,
                command=lambda c=c_name: self.assistant.smart_home.set_color(c),
                height=32,
            )
            btn.grid(row=0, column=idx, padx=3, sticky="nsew")

    def _on_slider_change(self, val: float) -> None:
        int_val = int(val)
        self.brightness_val_label.configure(text=f"{int_val}%")
        self.assistant.smart_home.set_brightness(int_val)

    def _on_save_device(self) -> None:
        self.assistant.config.smart_bulb_ip = self.ip_entry.get().strip()
        self.assistant.config.tapo_email = self.email_entry.get().strip()
        self.assistant.config.tapo_password = self.pass_entry.get().strip()
        save_config(self.assistant.config)
        self.assistant.reload_config(self.assistant.config)
        self.save_status.configure(text="✓ Device settings saved! Reconnecting...")
