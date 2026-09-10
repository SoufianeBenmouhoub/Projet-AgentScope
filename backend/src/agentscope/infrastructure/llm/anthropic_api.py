"""Adaptateur Anthropic pour le port de proposition de mapping.

Le second fournisseur réel du projet, à côté d'Ollama. Il pose exactement la même question
et relit la réponse de la même façon (voir :mod:`agentscope.infrastructure.llm.prompt`) :
c'est ce qui permet de comparer honnêtement les deux modèles sur un même fichier.

Le module s'appelle ``anthropic_api`` et non ``anthropic`` pour ne pas masquer la
bibliothèque du même nom lors d'une lecture rapide du dossier.

Ni le modèle ni la clé ne sont écrits ici : ils arrivent par la configuration.
"""

from __future__ import annotations

from typing import Any

import anthropic

from agentscope.application.ports.mapping_proposal import (
    ImportSample,
    MappingProposal,
    MappingProposalPort,
    MappingProposalUnavailable,
)
from agentscope.infrastructure.llm.prompt import build_prompt, parse_proposal

#: De quoi proposer une correspondance pour les seize champs du contrat, sans laisser une
#: réponse partie en digression coûter davantage.
MAX_TOKENS = 4096


class AnthropicMappingProposal(MappingProposalPort):
    """Propose un mapping via l'API Anthropic."""

    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None) -> None:
        self._model = model
        # Sans clé explicite, le client lit ANTHROPIC_API_KEY dans l'environnement. Aucune
        # clé n'est écrite dans le dépôt, ni ici ni ailleurs.
        self._client = anthropic.Anthropic(api_key=api_key, base_url=base_url)

    def propose_mapping(self, sample: ImportSample) -> MappingProposal:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": build_prompt(sample)}],
            )
        except anthropic.AnthropicError as error:
            raise MappingProposalUnavailable(
                f"Le fournisseur Anthropic n'a pas répondu ({error})."
            ) from error

        return parse_proposal(_text_of(response))


def _text_of(response: Any) -> str:
    """Recolle les blocs de texte de la réponse.

    Une réponse est une liste de blocs qui ne sont pas tous du texte ; lire `.text` sans
    regarder le type du bloc casserait dès que le modèle en produit un autre.
    """
    return "".join(block.text for block in response.content if block.type == "text")
