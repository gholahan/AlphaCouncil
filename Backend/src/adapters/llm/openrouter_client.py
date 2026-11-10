"""OpenRouter LLM Client Adapter using LangChain ChatOpenAI."""

import logging
from typing import Optional, Any
from langchain_openai import ChatOpenAI

from src.application.ports.outbound.llm_client import LLMClient
from src.config.settings import settings

logger = logging.getLogger(__name__)


class OpenRouterClientAdapter(LLMClient):
    """Adapter for OpenRouter models using LangChain's ChatOpenAI."""

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.default_model = default_model or settings.DEFAULT_OPENROUTER_MODEL

    def get_chat_model(self, model: Optional[str] = None, temperature: float = 0.7) -> Any:
        model_to_use = model or self.default_model
        return ChatOpenAI(
            model=model_to_use,
            temperature=temperature,
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://alphacouncil.app",
                "X-Title": "AlphaCouncil Investment Platform",
            },
        )
