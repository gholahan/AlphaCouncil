"""Groq LLM Client Adapter using LangChain ChatGroq."""

import logging
from typing import Optional, Any
from langchain_groq import ChatGroq

from src.application.ports.outbound.llm_client import LLMClient
from src.config.settings import settings

logger = logging.getLogger(__name__)


class GroqClientAdapter(LLMClient):
    """Adapter for Groq models using LangChain's ChatGroq."""

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.default_model = default_model or settings.DEFAULT_GROQ_MODEL

    def get_chat_model(self, model: Optional[str] = None, temperature: float = 0.7) -> Any:
        model_to_use = model or self.default_model
        return ChatGroq(
            model_name=model_to_use,
            temperature=temperature,
            api_key=self.api_key,
        )
