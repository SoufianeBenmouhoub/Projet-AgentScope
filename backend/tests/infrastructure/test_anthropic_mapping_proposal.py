"""Tests de l'adaptateur Anthropic : le client est doublé, aucun appel réseau, aucune clé.

La relecture de la réponse est testée une fois pour toutes dans `test_llm_prompt.py` ;
ce qui reste ici est propre à l'adaptateur — la forme de la requête, la lecture des blocs
de la réponse, et ce qu'il fait quand l'API refuse.
"""

from __future__ import annotations

from types import SimpleNamespace

import anthropic
import pytest

from agentscope.application.ports.mapping_proposal import (
    FieldSample,
    ImportSample,
    MappingProposalUnavailable,
)
from agentscope.infrastructure.llm.anthropic_api import MAX_TOKENS, AnthropicMappingProposal

A_SAMPLE = ImportSample(
    source_format="jsonl",
    fields=(FieldSample(name="session", example_values=("sess-1",)),),
)


def _adapter() -> AnthropicMappingProposal:
    # Une clé factice suffit : aucun appel ne sort, `messages.create` est remplacé.
    return AnthropicMappingProposal(model="test-model", api_key="cle-de-test")


def _response(*blocks: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(content=list(blocks))


def _text(value: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=value)


def test_interroge_le_modele_configure_avec_la_question_du_projet(monkeypatch) -> None:
    adapter = _adapter()
    sent: dict[str, object] = {}

    def capture(**kwargs):
        sent.update(kwargs)
        return _response(_text('{"mappings": []}'))

    monkeypatch.setattr(adapter._client.messages, "create", capture)

    adapter.propose_mapping(A_SAMPLE)

    assert sent["model"] == "test-model"
    assert sent["max_tokens"] == MAX_TOKENS
    assert "session_id" in sent["messages"][0]["content"]


def test_traduit_une_reponse_du_modele_en_proposition(monkeypatch) -> None:
    adapter = _adapter()
    payload = (
        '{"mappings": [{"target_field": "session_id", "source_field": "session", '
        '"confidence": 0.9, "note": "Nom proche"}]}'
    )
    monkeypatch.setattr(adapter._client.messages, "create", lambda **k: _response(_text(payload)))

    proposal = adapter.propose_mapping(A_SAMPLE)

    assert proposal.mappings[0].source_field == "session"


def test_ne_lit_que_les_blocs_de_texte_de_la_reponse(monkeypatch) -> None:
    """Une réponse est une liste de blocs qui ne sont pas tous du texte : lire `.text`
    sans regarder le type casserait dès que le modèle en produit un autre."""
    adapter = _adapter()
    autre_bloc = SimpleNamespace(type="thinking", thinking="réflexion interne")
    payload = '{"mappings": [{"target_field": "model", "source_field": "m", "confidence": 1.0}]}'
    monkeypatch.setattr(
        adapter._client.messages,
        "create",
        lambda **k: _response(autre_bloc, _text(payload)),
    )

    proposal = adapter.propose_mapping(A_SAMPLE)

    assert proposal.mappings[0].target_field == "model"


def test_une_api_qui_refuse_se_distingue_dune_absence_de_correspondance(monkeypatch) -> None:
    """Une clé invalide ne doit pas ressembler à « aucun champ ne correspond »."""
    adapter = _adapter()

    def refuse(**kwargs):
        raise anthropic.APIConnectionError(request=SimpleNamespace())

    monkeypatch.setattr(adapter._client.messages, "create", refuse)

    with pytest.raises(MappingProposalUnavailable) as error:
        adapter.propose_mapping(A_SAMPLE)

    assert "Anthropic" in str(error.value)
