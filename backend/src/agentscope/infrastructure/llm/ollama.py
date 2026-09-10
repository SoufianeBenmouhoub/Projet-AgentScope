"""Adaptateur Ollama pour le port de proposition de mapping.

Le fournisseur local du projet : aucune clé, aucun appel sortant, le modèle tourne sur la
machine. Ollama expose un point d'accès compatible OpenAI, d'où le client utilisé ici.

La question posée et la relecture de la réponse sont celles de
:mod:`agentscope.infrastructure.llm.prompt`, partagées avec l'adaptateur Anthropic.
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


class OllamaMappingProposal(MappingProposalPort):
    """Propose un mapping via un modèle exécuté localement avec Ollama."""

    def __init__(self, model: str, base_url: str) -> None:
        self._model = model
        # Ollama n'authentifie rien, mais le client OpenAI exige une clé non vide.
        self._client = openai.OpenAI(base_url=base_url, api_key="ollama")

    def propose_mapping(self, sample: ImportSample) -> MappingProposal:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": build_prompt(sample)}],
            )
        except openai.OpenAIError as error:
            raise MappingProposalUnavailable(
                f"Le serveur Ollama n'a pas répondu ({error}). Vérifiez qu'il tourne sur "
                "AI_BASE_URL et que AI_MODEL y est téléchargé."
            ) from error

        return parse_proposal(response.choices[0].message.content)
