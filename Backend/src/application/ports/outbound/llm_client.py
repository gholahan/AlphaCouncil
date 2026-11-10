"""LLM Client Port - Abstract interface for LLM adapters."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMClient(ABC):
    """Port for interacting with LLM providers using LangChain chat models."""

    @abstractmethod
    def get_chat_model(self, model: Optional[str] = None, temperature: float = 0.7) -> Any:
        """Return the underlying LangChain chat model instance."""
        pass
