"""
AI Assistant and Large Language Model Management Studio.
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

from ...core.config import save_config
from ...core.logger import get_logger

if TYPE_CHECKING:
    from ...core.assistant import LinnyAssistant

logger = get_logger("ui.ai")

COLOR_SURFACE = "#1A1A1A"
COLOR_SURFACE_ALT = "#242424"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_BORDER = "#444444"
COLOR_ACCENT = "#888888"
COLOR_BTN_BG = "#2A2A2A"
COLOR_BTN_HOVER = "#383838"


class AIView(ctk.CTkScrollableFrame):
    """AI Studio and Interactive Prompt Sandbox."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        # Title Header
        ctk.CTkLabel(
            self,
            text="Multi-Provider AI Studio",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Configure Groq, Google Gemini, and Perplexity with multi-model fallback and live prompt testing.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=28, pady=(0, 16))

        # Providers Hub Container
        hub_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        hub_frame.pack(fill="x", padx=28, pady=(0, 16))

        hub_inner = ctk.CTkFrame(hub_frame, fg_color="transparent")
        hub_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            hub_inner,
            text="API Credentials and Provider Setup",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 12))

        # 1. Groq
        groq_row = ctk.CTkFrame(hub_inner, fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        groq_row.pack(fill="x", pady=4)
        groq_inner = ctk.CTkFrame(groq_row, fg_color="transparent")
        groq_inner.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(
            groq_inner,
            text="Groq (Llama 3.3 70B)",
            width=180,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        self.groq_entry = ctk.CTkEntry(
            groq_inner,
            placeholder_text="Enter Groq API Key (gsk_...)",
            show="*",
            height=34,
            border_color=COLOR_BORDER,
            fg_color="#181818",
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
        )
        self.groq_entry.insert(0, self.assistant.config.groq_api_key)
        self.groq_entry.pack(side="left", fill="x", expand=True, padx=10)

        # 2. Gemini
        gem_row = ctk.CTkFrame(hub_inner, fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        gem_row.pack(fill="x", pady=4)
        gem_inner = ctk.CTkFrame(gem_row, fg_color="transparent")
        gem_inner.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(
            gem_inner,
            text="Google Gemini (Flash)",
            width=180,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        self.gemini_entry = ctk.CTkEntry(
            gem_inner,
            placeholder_text="Enter Gemini API Key (AIzaSy...)",
            show="*",
            height=34,
            border_color=COLOR_BORDER,
            fg_color="#181818",
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
        )
        self.gemini_entry.insert(0, self.assistant.config.gemini_api_key)
        self.gemini_entry.pack(side="left", fill="x", expand=True, padx=10)

        # 3. Perplexity
        perp_row = ctk.CTkFrame(hub_inner, fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        perp_row.pack(fill="x", pady=4)
        perp_inner = ctk.CTkFrame(perp_row, fg_color="transparent")
        perp_inner.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(
            perp_inner,
            text="Perplexity (Sonar Search)",
            width=180,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        self.perp_entry = ctk.CTkEntry(
            perp_inner,
            placeholder_text="Enter Perplexity API Key (pplx-...)",
            show="*",
            height=34,
            border_color=COLOR_BORDER,
            fg_color="#181818",
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
        )
        self.perp_entry.insert(0, self.assistant.config.perplexity_api_key)
        self.perp_entry.pack(side="left", fill="x", expand=True, padx=10)

        # Save Button Row
        save_row = ctk.CTkFrame(hub_inner, fg_color="transparent")
        save_row.pack(fill="x", pady=(12, 0))

        save_btn = ctk.CTkButton(
            save_row,
            text="Save AI Credentials",
            command=self._on_save_keys,
            width=160,
            height=36,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
        )
        save_btn.pack(side="left")

        self.save_status_label = ctk.CTkLabel(save_row, text="", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_SECONDARY)
        self.save_status_label.pack(side="left", padx=12)

        # Section 2: Interactive AI Sandbox
        box_card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, border_color=COLOR_BORDER, border_width=1, corner_radius=12)
        box_card.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        box_inner = ctk.CTkFrame(box_card, fg_color="transparent")
        box_inner.pack(fill="both", expand=True, padx=20, pady=18)

        # Sandbox Controls Header
        top_bar = ctk.CTkFrame(box_inner, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_bar,
            text="Live AI Chat and Reasoning Sandbox",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left")

        self.provider_select = ctk.CTkOptionMenu(
            top_bar,
            values=["Auto-Cascade (Recommended)", "Groq Llama 3.3", "Google Gemini", "Perplexity Sonar"],
            width=200,
            height=32,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            button_color=COLOR_BORDER,
            button_hover_color="#555555",
            corner_radius=6,
        )
        self.provider_select.pack(side="right")

        # Response Output Box
        self.response_text = ctk.CTkTextbox(
            box_inner,
            height=140,
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.response_text.pack(fill="both", expand=True, pady=(0, 10))
        self.response_text.insert("0.0", "AI responses and latency benchmarks will appear here.")

        # Latency / Token Meta Badge
        meta_row = ctk.CTkFrame(box_inner, fg_color="transparent")
        meta_row.pack(fill="x", pady=(0, 8))

        self.meta_label = ctk.CTkLabel(
            meta_row,
            text="Status: Ready",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.meta_label.pack(side="left")

        # Prompt Input & Action Buttons
        prompt_row = ctk.CTkFrame(box_inner, fg_color="transparent")
        prompt_row.pack(fill="x")

        self.prompt_entry = ctk.CTkEntry(
            prompt_row,
            placeholder_text="Enter test prompt (e.g. 'Explain how neural networks learn in 2 sentences')",
            height=38,
            font=ctk.CTkFont(size=12),
            border_color=COLOR_BORDER,
            fg_color=COLOR_SURFACE_ALT,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.prompt_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.prompt_entry.bind("<Return>", lambda e: self._on_send_prompt())

        test_run_btn = ctk.CTkButton(
            prompt_row,
            text="Run Query",
            command=self._on_send_prompt,
            width=95,
            height=38,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        test_run_btn.pack(side="left", padx=(0, 6))

        speak_btn = ctk.CTkButton(
            prompt_row,
            text="Speak",
            command=self._on_speak_response,
            width=70,
            height=38,
            fg_color=COLOR_BTN_BG,
            hover_color=COLOR_BTN_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
        )
        speak_btn.pack(side="right")

    def _on_save_keys(self) -> None:
        self.assistant.config.groq_api_key = self.groq_entry.get().strip()
        self.assistant.config.gemini_api_key = self.gemini_entry.get().strip()
        self.assistant.config.perplexity_api_key = self.perp_entry.get().strip()
        save_config(self.assistant.config)
        self.assistant.reload_config(self.assistant.config)
        self.save_status_label.configure(text="Credentials saved and activated.")

    def _on_send_prompt(self) -> None:
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return

        self._on_save_keys()
        self.meta_label.configure(text="Querying AI provider...", text_color=COLOR_TEXT_SECONDARY)
        self.response_text.delete("0.0", "end")
        self.response_text.insert("0.0", "Generating response...")

        mode = self.provider_select.get()

        def _worker():
            ans = ""
            elapsed = 0.0
            provider_tag = ""

            if "Groq" in mode:
                ans, elapsed = self.assistant.brain.ask_groq(prompt)
                provider_tag = "Groq Llama 3.3"
            elif "Gemini" in mode:
                ans, elapsed = self.assistant.brain.ask_gemini(prompt)
                provider_tag = "Google Gemini Flash"
            elif "Perplexity" in mode:
                ans, elapsed = self.assistant.brain.ask_perplexity(prompt)
                provider_tag = "Perplexity Sonar"
            else:
                import time
                start_t = time.time()
                ans = self.assistant.brain.ask(prompt)
                elapsed = time.time() - start_t
                provider_tag = "Auto-Cascade Engine"

            def _update():
                if not self.winfo_exists():
                    return
                self.response_text.delete("0.0", "end")
                self.response_text.insert("0.0", ans or "No response received.")
                self.meta_label.configure(
                    text=f"Delivered via {provider_tag} in {elapsed:.2f}s",
                    text_color=COLOR_TEXT_SECONDARY,
                )

            self.after(0, _update)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_speak_response(self) -> None:
        text = self.response_text.get("0.0", "end").strip()
        if text and "Generating" not in text:
            self.assistant.voice.speak(text)
