"""
Cascading Multi-Provider AI Brain.
Hierarchy:
1. Search / News / Realtime Fact Queries -> Perplexity Sonar API
2. General Chat / Queries -> Groq (Llama 3.3 70B Versatile)
3. Fallback AI -> Google Gemini (Gemini 2.0 Flash)
4. Offline Heuristics -> Local fallback
"""

from __future__ import annotations

import re
from typing import Optional

import requests

from ..core.config import LinnyConfig
from ..core.logger import get_logger

logger = get_logger("brain")


class AIBrain:
    """Cascading multi-model AI reasoning engine with lazy initialization."""

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

        # Initialize Groq
        if self.config.groq_api_key:
            try:
                import groq
                self._groq_client = groq.Groq(api_key=self.config.groq_api_key)
                logger.info("Groq API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")

        # Initialize Gemini
        if self.config.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.gemini_api_key)
                # Try gemini-2.0-flash, fallback to gemini-1.5-flash
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
            "stock", "crypto", "score", "today's news", "update on", "who won"
        ]
        q_lower = query.lower()
        return any(k in q_lower for k in keywords)

    def _ask_perplexity(self, query: str, system_prompt: str) -> Optional[str]:
        """Query Perplexity online search model."""
        if not self.config.perplexity_api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.config.perplexity_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                "max_tokens": 300,
            }
            resp = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()
                # Clean citation brackets like [1][2]
                cleaned = re.sub(r"\[\d+\]", "", answer).strip()
                logger.info("Perplexity answered query")
                return cleaned
            else:
                logger.warning(f"Perplexity returned status {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            logger.warning(f"Perplexity query failed: {e}")
            return None

    def _ask_groq(self, query: str, system_prompt: str) -> Optional[str]:
        """Query Groq ultra-fast Llama 3.3 model."""
        if not self._groq_client:
            return None

        try:
            response = self._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.7,
                max_tokens=250,
            )
            answer = response.choices[0].message.content.strip()
            logger.info("Groq answered query")
            return answer
        except Exception as e:
            logger.warning(f"Groq query failed: {e}")
            return None

    def _ask_gemini(self, query: str, system_prompt: str) -> Optional[str]:
        """Query Google Gemini model."""
        if not self._gemini_model:
            return None

        try:
            full_prompt = f"{system_prompt}\n\nUser Question: {query}"
            response = self._gemini_model.generate_content(full_prompt)
            if response and response.text:
                answer = response.text.strip()
                logger.info("Gemini answered query")
                return answer
            return None
        except Exception as e:
            logger.warning(f"Gemini query failed: {e}")
            return None

    def ask(self, query: str) -> str:
        """
        Execute cascading query execution.
        Returns concise, conversational speech-ready text.
        """
        self._init_clients()

        system_prompt = (
            f"You are Linny, a smart, loyal, concise personal AI assistant for {self.config.user_name}. "
            f"Language: {self.config.language}. "
            "Keep your responses natural, conversational, friendly, and concise (1 to 2 sentences max) "
            "suitable for text-to-speech voice output. Avoid markdown tables or bullet points."
        )

        # 1. Real-time Search queries -> Perplexity First
        if self.is_search_query(query):
            ans = self._ask_perplexity(query, system_prompt)
            if ans:
                return ans

        # 2. Fast Chat -> Groq
        ans = self._ask_groq(query, system_prompt)
        if ans:
            return ans

        # 3. Fallback AI -> Gemini
        ans = self._ask_gemini(query, system_prompt)
        if ans:
            return ans

        # 4. Search fallback if Groq/Gemini offline
        if not self.is_search_query(query) and self.config.perplexity_api_key:
            ans = self._ask_perplexity(query, system_prompt)
            if ans:
                return ans

        # 5. Offline Fallback Response
        logger.warning("All AI providers unavailable or not configured")
        return (
            "I'm sorry, I couldn't reach any AI services right now. "
            "Please check your internet connection or API keys in Settings."
        )
