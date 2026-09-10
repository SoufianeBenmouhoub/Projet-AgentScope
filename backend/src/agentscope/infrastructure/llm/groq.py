"""Adaptateur Groq pour le port de proposition de mapping.

Un fournisseur cloud gratuit, avec une API compatible OpenAI — comme Ollama. Contrairement
à Ollama, il ne demande aucune installation locale : n'importe qui (coéquipier,
correcteur) peut le tester en repartant du dépôt avec sa propre clé.

La question posée et la relecture de la réponse sont celles de
:mod:`agentscope.infrastructure.llm.prompt`, partagées avec les autres adaptateurs.
"""

from __future__ import annotations

import openai

from agentscope.application.ports.mapping_proposal import (
    ImportSample,
    MappingProposal,
    MappingProposalPort,
    MappingProposalUnavailable,
)
from agentscope.infrastructure.llm.prompt import build_prompt, parse_proposal

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"


class GroqMappingProposal(MappingProposalPort):
    """Propose un mapping via l'API cloud gratuite de Groq."""

    def __init__(self, model: str, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        self._model = model
        self._client = openai.OpenAI(base_url=base_url, api_key=api_key)

    def propose_mapping(self, sample: ImportSample) -> MappingProposal:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": build_prompt(sample)}],
            )
        except openai.OpenAIError as error:
            raise MappingProposalUnavailable(
                f"Groq n'a pas répondu ({error}). Vérifiez AI_API_KEY et AI_MODEL."
            ) from error

        return parse_proposal(response.choices[0].message.content)
