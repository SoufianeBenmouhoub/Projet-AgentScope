"""Adaptateur Ollama pour le port de proposition de mapping."""

from __future__ import annotations

from agentscope.infrastructure.llm.base import OpenAICompatibleMappingProposal


class OllamaMappingProposal(OpenAICompatibleMappingProposal):
    """Propose un mapping via un modèle exécuté localement avec Ollama."""

    def __init__(self, model: str, base_url: str) -> None:
        super().__init__(model=model, api_key="ollama", base_url=base_url)
