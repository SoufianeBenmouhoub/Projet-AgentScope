"""Tests d'API : la route de proposition de mapping tourne avec la doublure `fake`."""

from __future__ import annotations

from tests.interfaces.client import build_client


def test_propose_un_mapping_a_partir_dechantillons_bruts() -> None:
    response = build_client().post(
        "/api/v1/mapping/propose",
        json={
            "source_format": "jsonl",
            "records": [
                {"session": "sess-1", "tool": "bash"},
                {"session": "sess-2", "tool": "read_file"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()

    names = {m["target_field"] for m in body["mappings"]}
    assert names == {"session", "tool"}
    # La doublure `fake` propose toujours le champ source identique au champ cible.
    assert all(m["source_field"] == m["target_field"] for m in body["mappings"])
    assert all(m["confidence"] == 1.0 for m in body["mappings"])


def test_un_echantillon_vide_repond_sans_erreur() -> None:
    """Aucune donnée importée doit répondre « rien », pas planter."""
    response = build_client().post(
        "/api/v1/mapping/propose",
        json={"source_format": "csv", "records": []},
    )

    assert response.status_code == 200
    assert response.json() == {"mappings": [], "unresolved_notes": []}
