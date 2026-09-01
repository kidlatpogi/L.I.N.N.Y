"""
Cascading Multi-Provider AI Brain.
Hierarchy:
1. Search / News / Realtime Fact Queries -> Perplexity Sonar API
2. General Chat / Dialogue -> Groq (Llama 3.3 70B Versatile)
3. Fallback AI -> Google Gemini (Gemini 2.0 Flash)
4. Offline Heuristics -> Local fallback
"""

from __future__ import annotations

import re
import time
from typing import Dict, Optional, Tuple

import requests

from ..core.config import LinnyConfig
from ..core.logger import get_logger

logger = get_logger("brain")


class AIBrain:
    """Cascading multi-model AI reasoning engine with interactive provider execution."""

    def __init__(self, config: LinnyConfig) -> None:
        self.config = config
        self._groq_client = None
        self._gemini_model = None
        self._initialized = False

    def reload(self, config: LinnyConfig) -> None:
        """Reload configuration and reset cached API clients."""
        self.config = config
        self._groq_client = None
        self._gemini_model = None
        self._initialized = False

    def _init_clients(self) -> None:
        """Lazily initialize AI clients only when needed."""
        if self._initialized:
            return

        if self.config.groq_api_key:
            try:
                import groq
                self._groq_client = groq.Groq(api_key=self.config.groq_api_key)
                logger.info("Groq API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

        if self.config.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.gemini_api_key)
                try:
                    self._gemini_model = genai.GenerativeModel("gemini-2.0-flash")
                except Exception:
                    self._gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Google Gemini model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini model: {e}")

        self._initialized = True

    def is_search_query(self, query: str) -> bool:
        """Detect whether a query requires live web search."""
        keywords = [
            "search", "price", "news", "latest", "who is", "what is the current",
            "stock", "crypto", "score", "today's news", "update on", "who won", "live"
        ]
        q_lower = query.lower()
        return any(k in q_lower for k in keywords)

    def ask_perplexity(self, query: str, model: str = "llama-3.1-sonar-small-128k-online") -> Tuple[Optional[str], float]:
        """Query Perplexity online search model directly with latency measurement."""
        if not self.config.perplexity_api_key:
            return None, 0.0

        start_t = time.time()
        try:
            headers = {
                "Authorization": f"Bearer {self.config.perplexity_api_key}",
                "Content-Type": "application/json",
            }
            system_prompt = (
                f"You are Linny, a smart AI assistant for {self.config.user_name}. "
                f"Language: {self.config.language}. Be concise, conversational, and factual (1 to 2 sentences max)."
            )
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                "max_tokens": 250,
            }
            resp = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=10,
            )
            elapsed = time.time() - start_t
            if resp.status_code == 200:
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()
                cleaned = re.sub(r"\[\d+\]", "", answer).strip()
                logger.info(f"Perplexity answered in {elapsed:.2f}s")
                return cleaned, elapsed
            return None, elapsed
        except Exception as e:
            logger.warning(f"Perplexity query failed: {e}")
            return None, time.time() - start_t

    def ask_groq(self, query: str, model: str = "llama-3.3-70b-versatile") -> Tuple[Optional[str], float]:
        """Query Groq model directly with latency measurement."""
        self._init_clients()
        if not self._groq_client:
            return None, 0.0

        start_t = time.time()
        try:
            system_prompt = (
                f"You are Linny, a smart, concise AI assistant for {self.config.user_name}. "
                f"Language: {self.config.language}. Keep response friendly and concise (1 to 2 sentences max)."
            )
            response = self._groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.7,
                max_tokens=250,
            )
            elapsed = time.time() - start_t
            answer = response.choices[0].message.content.strip()
            logger.info(f"Groq ({model}) answered in {elapsed:.2f}s")
            return answer, elapsed
        except Exception as e:
            logger.warning(f"Groq query failed: {e}")
            return None, time.time() - start_t

    def ask_gemini(self, query: str) -> Tuple[Optional[str], float]:
        """Query Google Gemini model directly with latency measurement."""
        self._init_clients()
        if not self._gemini_model:
            return None, 0.0

        start_t = time.time()
        try:
            system_prompt = (
                f"You are Linny, an AI assistant for {self.config.user_name}. "
                f"Language: {self.config.language}. Be concise, friendly, and natural for voice speech (1-2 sentences)."
            )
            full_prompt = f"{system_prompt}\n\nUser Question: {query}"
            response = self._gemini_model.generate_content(full_prompt)
            elapsed = time.time() - start_t
            if response and response.text:
                return response.text.strip(), elapsed
            return None, elapsed
        except Exception as e:
            logger.warning(f"Gemini query failed: {e}")
            return None, time.time() - start_t

    def ask(self, query: str) -> str:
        """Execute cascading multi-LLM query execution."""
        # 1. Search / News -> Perplexity First
        if self.is_search_query(query):
            ans, _ = self.ask_perplexity(query)
            if ans:
                return ans

        # 2. Fast Chat -> Groq
        ans, _ = self.ask_groq(query)
        if ans:
            return ans

        # 3. Secondary AI -> Gemini
        ans, _ = self.ask_gemini(query)
        if ans:
            return ans

        # 4. Search fallback
        if self.config.perplexity_api_key:
            ans, _ = self.ask_perplexity(query)
            if ans:
                return ans

        # 5. Offline Fallback
        return (
            "I couldn't reach any configured AI services right now. "
            "Please verify your API keys or internet connection in the AI Assistants tab."
        )
