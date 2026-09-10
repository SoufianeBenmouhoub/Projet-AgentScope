"""Tests de l'adaptateur Groq : la réponse du modèle est simulée, aucun appel réseau.

La relecture de la réponse est testée une fois pour toutes dans `test_llm_prompt.py` ;
ce qui reste ici est propre à l'adaptateur — ce qu'il envoie, et ce qu'il fait quand le
service cloud ne répond pas.
"""

from __future__ import annotations

from types import SimpleNamespace

import openai
import pytest

from agentscope.application.ports.mapping_proposal import (
    FieldSample,
    ImportSample,
    MappingProposalUnavailable,
)
from agentscope.infrastructure.llm.groq import GroqMappingProposal

A_SAMPLE = ImportSample(
    source_format="jsonl",
    fields=(FieldSample(name="session", example_values=("sess-1",)),),
)


def _adapter() -> GroqMappingProposal:
    return GroqMappingProposal(model="test-model", api_key="test-key")


def _response(content: str) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_interroge_le_modele_configure_avec_la_question_du_projet(monkeypatch) -> None:
    adapter = _adapter()
    sent: dict[str, object] = {}

    def capture(**kwargs):
        sent.update(kwargs)
        return _response('{"mappings": []}')

    monkeypatch.setattr(adapter._client.chat.completions, "create", capture)

    adapter.propose_mapping(A_SAMPLE)

    assert sent["model"] == "test-model"
    assert "session_id" in sent["messages"][0]["content"]


def test_traduit_une_reponse_du_modele_en_proposition(monkeypatch) -> None:
    adapter = _adapter()
    payload = (
        '{"mappings": [{"target_field": "session_id", "source_field": "session", '
        '"confidence": 0.9, "note": "Nom proche"}]}'
    )
    monkeypatch.setattr(
        adapter._client.chat.completions, "create", lambda **kwargs: _response(payload)
    )

    proposal = adapter.propose_mapping(A_SAMPLE)

    assert proposal.mappings[0].source_field == "session"


def test_un_service_injoignable_se_distingue_dune_absence_de_correspondance(monkeypatch) -> None:
    """Renvoyer une proposition vide ferait croire que le fichier ne ressemble à rien,
    alors que c'est Groq qui n'a pas répondu."""
    adapter = _adapter()

    def refuse(**kwargs):
        raise openai.APIConnectionError(request=SimpleNamespace())

    monkeypatch.setattr(adapter._client.chat.completions, "create", refuse)

    with pytest.raises(MappingProposalUnavailable) as error:
        adapter.propose_mapping(A_SAMPLE)

    assert "AI_API_KEY" in str(error.value)
