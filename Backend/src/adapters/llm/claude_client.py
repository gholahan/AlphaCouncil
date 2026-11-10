"""Claude LLM Client Adapter - Implementation of LLMClient port using Anthropic API."""

import logging
import os
from typing import List, Dict, Any, Optional, AsyncIterator

from src.application.ports.outbound.llm_client import LLMClient
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ClaudeClientAdapter(LLMClient):
    """Adapter for interacting with Anthropic Claude models."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None) or os.getenv("ANTHROPIC_API_KEY")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate completion using Anthropic API."""
        # Stub implementation delegating or calling Anthropic SDK if desired
        return {
            "content": "Claude direct generation stub",
            "tool_calls": [],
            "usage": {"total_tokens": 100},
            "finish_reason": "end_turn",
        }

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream completion."""
        if False:
            yield ""

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
