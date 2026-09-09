"""Tests de l'adaptateur Ollama : la réponse du modèle est simulée, aucun appel réseau."""

from __future__ import annotations

from types import SimpleNamespace

from agentscope.application.ports.mapping_proposal import FieldSample, ImportSample
from agentscope.infrastructure.llm.ollama import OllamaMappingProposal


def _fake_response(content: str) -> SimpleNamespace:
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def test_analyse_une_reponse_valide_avec_notes(monkeypatch) -> None:
    adapter = OllamaMappingProposal(model="test-model", base_url="http://localhost:11434/v1")
    payload = (
        '{"mappings": ['
        '{"target_field": "session_id", "source_field": "session", '
        '"confidence": 0.9, "note": "Nom proche et valeurs cohérentes"},'
        '{"target_field": "latency_ms", "source_field": null, '
        '"confidence": null, "note": "Aucun champ ne s\'en approche"}'
        "]}"
    )
    monkeypatch.setattr(
        adapter._client.chat.completions, "create", lambda **kwargs: _fake_response(payload)
    )

    sample = ImportSample(
        source_format="jsonl",
        fields=(FieldSample(name="session", example_values=("sess-1",)),),
    )
    proposal = adapter.propose_mapping(sample)

    assert len(proposal.mappings) == 2
    assert proposal.mappings[0].note == "Nom proche et valeurs cohérentes"
    assert proposal.unresolved_notes == ("latency_ms : Aucun champ ne s'en approche",)


def test_une_reponse_json_invalide_est_signalee_sans_planter(monkeypatch) -> None:
    adapter = OllamaMappingProposal(model="test-model", base_url="http://localhost:11434/v1")
    monkeypatch.setattr(
        adapter._client.chat.completions,
        "create",
        lambda **kwargs: _fake_response("pas du json valide"),
    )

    sample = ImportSample(source_format="csv", fields=())
    proposal = adapter.propose_mapping(sample)

    assert proposal.mappings == ()
    assert proposal.unresolved_notes
    assert "Réponse IA non exploitable" in proposal.unresolved_notes[0]
