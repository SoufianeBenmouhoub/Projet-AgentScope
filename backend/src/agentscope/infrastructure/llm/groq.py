"""Adaptateur Groq (API cloud gratuite, compatible OpenAI) pour le port de
proposition de mapping."""

from __future__ import annotations

from agentscope.infrastructure.llm.base import OpenAICompatibleMappingProposal

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"


class GroqMappingProposal(OpenAICompatibleMappingProposal):
    """Propose un mapping via l'API cloud gratuite de Groq."""

    def __init__(self, model: str, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)
