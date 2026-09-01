"""
AI Assistant and Large Language Model Management View.
Configure Groq, Google Gemini, and Perplexity API keys and test response pipelines.
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


class AIView(ctk.CTkScrollableFrame):
    """AI Providers configuration view."""

    def __init__(self, parent: Any, assistant: LinnyAssistant) -> None:
        super().__init__(parent, fg_color="transparent")
        self.assistant = assistant
        self._build_ui()

    def _build_ui(self) -> None:
        # Title
        ctk.CTkLabel(
            self,
            text="🧠 Multi-Provider AI Brain",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            self,
            text="Linny cascades across Groq, Google Gemini, and Perplexity for fast, intelligent voice responses.",
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Groq Section
        groq_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        groq_card.pack(fill="x", padx=20, pady=(0, 15))

        groq_inner = ctk.CTkFrame(groq_card, fg_color="transparent")
        groq_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            groq_inner,
            text="⚡ Groq (Llama 3.3 70B Versatile) - Primary Fast Chat",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            groq_inner,
            text="Sub-second reasoning speed for voice dialogue and general commands.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(anchor="w", pady=(0, 10))

        self.groq_entry = ctk.CTkEntry(
            groq_inner,
            placeholder_text="gsk_...",
            show="*",
            height=38,
            font=ctk.CTkFont(size=12),
        )
        self.groq_entry.insert(0, self.assistant.config.groq_api_key)
        self.groq_entry.pack(fill="x")

        # Gemini Section
        gemini_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        gemini_card.pack(fill="x", padx=20, pady=(0, 15))

        gemini_inner = ctk.CTkFrame(gemini_card, fg_color="transparent")
        gemini_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            gemini_inner,
            text="✨ Google Gemini (Gemini 2.0 Flash) - Secondary Intelligence",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            gemini_inner,
            text="High-context fallback model for nuanced questions and reasoning.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(anchor="w", pady=(0, 10))

        self.gemini_entry = ctk.CTkEntry(
            gemini_inner,
            placeholder_text="AIzaSy...",
            show="*",
            height=38,
            font=ctk.CTkFont(size=12),
        )
        self.gemini_entry.insert(0, self.assistant.config.gemini_api_key)
        self.gemini_entry.pack(fill="x")

        # Perplexity Section
        perp_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        perp_card.pack(fill="x", padx=20, pady=(0, 20))

        perp_inner = ctk.CTkFrame(perp_card, fg_color="transparent")
        perp_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            perp_inner,
            text="🌐 Perplexity Sonar - Live Web & Real-Time Search",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            perp_inner,
            text="Powers real-time queries for news, stock/crypto prices, sports scores, and search facts.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(anchor="w", pady=(0, 10))

        self.perp_entry = ctk.CTkEntry(
            perp_inner,
            placeholder_text="pplx-...",
            show="*",
            height=38,
            font=ctk.CTkFont(size=12),
        )
        self.perp_entry.insert(0, self.assistant.config.perplexity_api_key)
        self.perp_entry.pack(fill="x")

        # Save and Test Actions
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 20))

        save_btn = ctk.CTkButton(
            btn_bar,
            text="Save AI Keys",
            command=self._on_save,
            width=140,
            height=40,
            fg_color="#06b6d4",
            hover_color="#0891b2",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        save_btn.pack(side="left", padx=(0, 10))

        test_btn = ctk.CTkButton(
            btn_bar,
            text="Test AI Query",
            command=self._on_test_ai,
            width=140,
            height=40,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        test_btn.pack(side="left")

        self.ai_status_label = ctk.CTkLabel(
            btn_bar,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#22c55e",
        )
        self.ai_status_label.pack(side="left", padx=15)

    def _on_save(self) -> None:
        self.assistant.config.groq_api_key = self.groq_entry.get().strip()
        self.assistant.config.gemini_api_key = self.gemini_entry.get().strip()
        self.assistant.config.perplexity_api_key = self.perp_entry.get().strip()
        save_config(self.assistant.config)
        self.assistant.reload_config(self.assistant.config)
        self.ai_status_label.configure(text="✓ AI settings saved and active!", text_color="#22c55e")

    def _on_test_ai(self) -> None:
        self._on_save()
        self.ai_status_label.configure(text="Querying AI Brain...", text_color="#f59e0b")

        def _test_worker():
            ans = self.assistant.brain.ask("Give me a one sentence cheerful greeting.")

            def _update():
                if self.winfo_exists():
                    self.ai_status_label.configure(text="✓ Test Successful!", text_color="#22c55e")
                self.assistant.voice.speak(ans)

            self.after(0, _update)

        threading.Thread(target=_test_worker, daemon=True).start()
