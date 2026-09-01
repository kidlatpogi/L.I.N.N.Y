"""
Smart Home Management View for Tapo and TP-Link Kasa Devices.
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
from typing import TYPE_CHECKING, Any, Dict, List

import customtkinter as ctk

from ...core.config import save_config
from ...core.logger import get_logger
from ...integrations.smart_home import DEVICE_FAMILIES

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.smarthome")

COLOR_SURFACE = "#1A1A1A"
COLOR_SURFACE_ALT = "#242424"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


class SmartHomeView(ctk.CTkScrollableFrame):
    """Smart home device picker and live lighting dashboard."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self.discovered_devices: List[Dict[str, Any]] = []
        self._brightness_timer: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Title Header
        ctk.CTkLabel(
            self,
            text="Smart Lighting (Tapo and Kasa)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Discover, configure, and control Tapo and TP-Link Kasa smart devices.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=28, pady=(0, 16))

        # Device Setup & Network Scanner Card
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="x", padx=28, pady=(0, 16))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=18)

        # Scanner Header Row
        scan_row = ctk.CTkFrame(inner, fg_color="transparent")
        scan_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            scan_row,
            text="Device Discovery and Network Setup",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        self.scan_btn = ctk.CTkButton(
            scan_row,
            text="Scan Network",
            command=self._on_scan_network,
            width=120,
            height=32,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        self.scan_btn.pack(side="right")

        # Pick Device Dropdown
        pick_row = ctk.CTkFrame(inner, fg_color="transparent")
        pick_row.pack(fill="x", pady=4)
        ctk.CTkLabel(pick_row, text="Select Device:", width=160, anchor="w", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).pack(side="left")

        self.device_picker = ctk.CTkOptionMenu(
            pick_row,
            values=[f"{self.assistant.config.smart_bulb_ip} (Configured Target)"],
            command=self._on_device_picked,
            height=34,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            button_color=COLOR_BORDER,
            button_hover_color="#555555",
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_SURFACE_ALT,
        )
        self.device_picker.pack(side="left", fill="x", expand=True)

        # Manual IP Entry
        ip_row = ctk.CTkFrame(inner, fg_color="transparent")
        ip_row.pack(fill="x", pady=4)
        ctk.CTkLabel(ip_row, text="Device IP Address:", width=160, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.ip_entry = ctk.CTkEntry(ip_row, placeholder_text="192.168.18.12", height=34, font=ctk.CTkFont(size=12), border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_PRIMARY)
        self.ip_entry.insert(0, self.assistant.config.smart_bulb_ip)
        self.ip_entry.pack(side="left", fill="x", expand=True)

        # Device Type / Family
        family_row = ctk.CTkFrame(inner, fg_color="transparent")
        family_row.pack(fill="x", pady=4)
        ctk.CTkLabel(family_row, text="Device Family:", width=160, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")

        family_names = list(DEVICE_FAMILIES.keys())
        current_family_display = family_names[0]
        for name, val in DEVICE_FAMILIES.items():
            if val == self.assistant.config.smart_bulb_family:
                current_family_display = name
                break

        self.family_var = ctk.StringVar(value=current_family_display)
        self.family_menu = ctk.CTkOptionMenu(
            family_row,
            variable=self.family_var,
            values=family_names,
            height=34,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            button_color=COLOR_BORDER,
            button_hover_color="#555555",
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_SURFACE_ALT,
        )
        self.family_menu.pack(side="left", fill="x", expand=True)

        # Tapo Credentials
        auth_row1 = ctk.CTkFrame(inner, fg_color="transparent")
        auth_row1.pack(fill="x", pady=4)
        ctk.CTkLabel(auth_row1, text="Tapo Email (TP-Link ID):", width=160, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.email_entry = ctk.CTkEntry(auth_row1, placeholder_text="Email used in Tapo App", height=34, font=ctk.CTkFont(size=12), border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_PRIMARY)
        self.email_entry.insert(0, self.assistant.config.tapo_email)
        self.email_entry.pack(side="left", fill="x", expand=True)

        auth_row2 = ctk.CTkFrame(inner, fg_color="transparent")
        auth_row2.pack(fill="x", pady=4)
        ctk.CTkLabel(auth_row2, text="Tapo Cloud Password:", width=160, anchor="w", text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        self.pass_entry = ctk.CTkEntry(auth_row2, placeholder_text="Password", show="*", height=34, font=ctk.CTkFont(size=12), border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ALT, text_color=COLOR_TEXT_PRIMARY)
        self.pass_entry.insert(0, self.assistant.config.tapo_password)
        self.pass_entry.pack(side="left", fill="x", expand=True)

        hint_label = ctk.CTkLabel(
            inner,
            text="Note: If 403 occurs with Tapo L530/L535 bulbs, enable 'Third-Party Compatibility' in Tapo App > Settings > Advanced Settings (or configure a local Device Account).",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=620,
            justify="left",
        )
        hint_label.pack(anchor="w", pady=(8, 4))

        # Action Buttons
        act_row = ctk.CTkFrame(inner, fg_color="transparent")
        act_row.pack(fill="x", pady=(8, 0))

        save_btn = ctk.CTkButton(
            act_row,
            text="Save and Bind Device",
            command=self._on_save_device,
            width=160,
            height=36,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        save_btn.pack(side="left", padx=(0, 8))

        test_btn = ctk.CTkButton(
            act_row,
            text="Test Connection",
            command=self._on_test_connection,
            width=130,
            height=36,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        test_btn.pack(side="left")

        self.status_feedback = ctk.CTkLabel(act_row, text="", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_SECONDARY)
        self.status_feedback.pack(side="left", padx=12)

        # Section 2: Interactive Lighting Studio Card
        ctrl_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        ctrl_card.pack(fill="x", padx=28, pady=(0, 24))

        ctrl_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            ctrl_inner,
            text="Live Lighting Controls and Color Presets",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 12))

        # Power Toggle Buttons
        p_row = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        p_row.pack(fill="x", pady=(0, 14))

        on_btn = ctk.CTkButton(
            p_row,
            text="Turn ON Light",
            command=lambda: self.assistant.smart_home.turn_on(),
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
        )
        on_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        off_btn = ctk.CTkButton(
            p_row,
            text="Turn OFF Light",
            command=lambda: self.assistant.smart_home.turn_off(),
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
        )
        off_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Brightness Slider
        ctk.CTkLabel(ctrl_inner, text="Brightness Level:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        slider_row = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        slider_row.pack(fill="x", pady=(0, 14))

        self.brightness_slider = ctk.CTkSlider(
            slider_row,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self._on_slider_change,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_TEXT_PRIMARY,
            progress_color=COLOR_ACCENT,
        )
        self.brightness_slider.set(100)
        self.brightness_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.brightness_val_label = ctk.CTkLabel(slider_row, text="100%", width=45, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_PRIMARY)
        self.brightness_val_label.pack(side="right")

        # Preset Modes
        ctk.CTkLabel(ctrl_inner, text="Lighting Modes:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(4, 6))
        mode_row = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 14))
        mode_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        modes = ["Focus", "Movie", "Gaming", "Night", "Relax"]
        for idx, m_name in enumerate(modes):
            btn = ctk.CTkButton(
                mode_row,
                text=m_name,
                fg_color=COLOR_BTN_BG,
                hover_color=COLOR_BTN_HOVER,
                text_color=COLOR_TEXT_PRIMARY,
                border_color=COLOR_BORDER,
                border_width=1,
                command=lambda m=m_name: self.assistant.smart_home.set_mode(m),
                height=32,
                corner_radius=6,
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            btn.grid(row=0, column=idx, padx=3, sticky="nsew")

        # Color Swatches
        ctk.CTkLabel(ctrl_inner, text="Color Presets:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(4, 6))
        color_row = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        color_row.pack(fill="x", pady=(0, 4))
        color_row.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        colors = ["Red", "Blue", "Green", "Cyan", "Violet", "Warm White"]
        for idx, c_name in enumerate(colors):
            btn = ctk.CTkButton(
                color_row,
                text=c_name,
                fg_color=COLOR_BTN_BG,
                hover_color=COLOR_BTN_HOVER,
                text_color=COLOR_TEXT_PRIMARY,
                border_color=COLOR_BORDER,
                border_width=1,
                command=lambda c=c_name: self.assistant.smart_home.set_color(c),
                height=30,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
            )
            btn.grid(row=0, column=idx, padx=3, sticky="nsew")

    def _on_scan_network(self) -> None:
        self.scan_btn.configure(text="Scanning...", state="disabled")
        self.status_feedback.configure(text="Scanning local LAN for smart devices...", text_color=COLOR_TEXT_SECONDARY)

        def _worker():
            devs = self.assistant.smart_home.scan_network_devices()
            self.discovered_devices = devs

            def _update():
                if not self.winfo_exists():
                    return
                self.scan_btn.configure(text="Scan Network", state="normal")
                if devs:
                    options = [f"{d['ip']} - {d['alias']} ({d.get('model', 'Tapo')})" for d in devs]
                    self.device_picker.configure(values=options)
                    self.device_picker.set(options[0])
                    self._on_device_picked(options[0])
                    self.status_feedback.configure(text=f"Found {len(devs)} smart device(s).", text_color=COLOR_TEXT_PRIMARY)
                else:
                    self.status_feedback.configure(text="No devices found via broadcast. Enter IP manually.", text_color=COLOR_TEXT_SECONDARY)

            self.after(0, _update)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_device_picked(self, choice: str) -> None:
        ip = choice.split(" ")[0].strip()
        self.ip_entry.delete(0, "end")
        self.ip_entry.insert(0, ip)

    def _on_save_device(self) -> None:
        self.assistant.config.smart_bulb_ip = self.ip_entry.get().strip()
        selected_family_display = self.family_var.get()
        self.assistant.config.smart_bulb_family = DEVICE_FAMILIES.get(selected_family_display, "SMART.TAPOBULB")
        self.assistant.config.tapo_email = self.email_entry.get().strip()
        self.assistant.config.tapo_password = self.pass_entry.get().strip()

        save_config(self.assistant.config)
        self.assistant.reload_config(self.assistant.config)
        self.status_feedback.configure(text="Device parameters saved. Reconnecting...", text_color=COLOR_TEXT_SECONDARY)

    def _on_test_connection(self) -> None:
        self._on_save_device()
        self.status_feedback.configure(text="Testing connection...", text_color=COLOR_TEXT_SECONDARY)

        def _on_result(success: bool, msg: str) -> None:
            def _update():
                if not self.winfo_exists():
                    return
                if success:
                    self.status_feedback.configure(text=f"Success: {msg}", text_color=COLOR_TEXT_PRIMARY)
                else:
                    self.status_feedback.configure(text=f"Failed: {msg}", text_color="#E08080")

            self.after(0, _update)

        self.assistant.smart_home.test_connection_async(_on_result)

    def _on_slider_change(self, val: float) -> None:
        int_val = int(val)
        self.brightness_val_label.configure(text=f"{int_val}%")

        if self._brightness_timer is not None:
            try:
                self.after_cancel(self._brightness_timer)
            except Exception:
                pass

        def _send():
            self.assistant.smart_home.set_brightness(int_val)
            self._brightness_timer = None

        self._brightness_timer = self.after(200, _send)
