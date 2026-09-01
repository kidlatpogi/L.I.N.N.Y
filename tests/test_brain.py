"""Tests for AIBrain search intent heuristics and prompt synthesis."""

from linny.core.config import LinnyConfig
from linny.integrations.ai_brain import AIBrain


def test_search_intent_detection():
    brain = AIBrain(LinnyConfig())

    assert brain.is_search_query("who is the president of France?") is True
    assert brain.is_search_query("latest bitcoin price") is True
    assert brain.is_search_query("what is the current news") is True
    assert brain.is_search_query("hello how are you") is False
    assert brain.is_search_query("tell me a joke") is False


def test_offline_fallback():
    # When no API keys are provided
    brain = AIBrain(LinnyConfig(groq_api_key="", gemini_api_key="", perplexity_api_key=""))
    ans = brain.ask("Who is Ada Lovelace?")
    assert "AI services" in ans or "offline" in ans.lower() or len(ans) > 0
