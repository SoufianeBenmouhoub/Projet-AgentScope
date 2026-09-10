"""Tests pour l'adaptateur Groq — aucun appel réseau réel (monkeypatch)."""

from __future__ import annotations

import json
from types import SimpleNamespace

from agentscope.application.ports.mapping_proposal import FieldSample, ImportSample
from agentscope.infrastructure.llm.groq import GroqMappingProposal


def _fake_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _sample() -> ImportSample:
    return ImportSample(
        source_format="jsonl",
        fields=(
            FieldSample(name="id_session", example_values=("abc123", "abc124")),
            FieldSample(name="horodatage", example_values=("2026-01-01T10:00:00Z",)),
        ),
    )


def test_analyse_une_reponse_valide_avec_notes(monkeypatch):
    adapter = GroqMappingProposal(model="llama-3.3-70b-versatile", api_key="test-key")

    valid_json = json.dumps(
        {
            "mappings": [
                {
                    "target_field": "session_id",
                    "source_field": "id_session",
                    "confidence": 0.95,
                    "note": "Correspondance évidente sur le nom du champ.",
                },
                {
                    "target_field": "model",
                    "source_field": None,
                    "confidence": 0.0,
                    "note": "Aucun champ du fichier ne correspond à un nom de modèle.",
                },
            ]
        }
    )

    monkeypatch.setattr(
        adapter._client.chat.completions,
        "create",
        lambda **kwargs: _fake_response(valid_json),
    )

    result = adapter.propose_mapping(_sample())

    assert len(result.mappings) == 2
    assert result.mappings[0].source_field == "id_session"
    assert result.mappings[0].confidence == 0.95
    assert result.mappings[1].source_field is None
    assert len(result.unresolved_notes) == 1
    assert "model" in result.unresolved_notes[0]


def test_une_reponse_json_invalide_est_signalee_sans_planter(monkeypatch):
    adapter = GroqMappingProposal(model="llama-3.3-70b-versatile", api_key="test-key")

    monkeypatch.setattr(
        adapter._client.chat.completions,
        "create",
        lambda **kwargs: _fake_response("ceci n'est pas du JSON"),
    )

    result = adapter.propose_mapping(_sample())

    assert result.mappings == ()
    assert len(result.unresolved_notes) == 1
    assert "non exploitable" in result.unresolved_notes[0]
