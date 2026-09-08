"""Tests de la route de détail d'une session."""

from __future__ import annotations

from tests.application.builders import model_call, session, tool_call
from tests.interfaces.client import build_client


def test_expose_le_detail_et_la_chronologie_dune_session() -> None:
    client = build_client(
        sessions=[session("s1", duration_minutes=15)],
        model_calls=[model_call("s1", input_tokens=100)],
        tool_calls=[tool_call("s1", tool_name="bash", is_error=True)],
    )

    payload = client.get("/api/v1/sessions/s1").json()

    assert payload["session_id"] == "s1"
    assert payload["model_calls"] == 1
    assert payload["tool_calls"] == 1
    assert payload["failed_tool_calls"] == 1
    assert len(payload["events"]) == 2
    assert payload["duration"]["value"] == 900


def test_une_session_sans_horodatage_a_une_duree_null_et_non_zero() -> None:
    client = build_client(sessions=[session("s1", dated=False)])

    duration = client.get("/api/v1/sessions/s1").json()["duration"]

    assert duration["value"] is None
    assert duration["available"] is False


def test_une_issue_dappel_inconnue_reste_null() -> None:
    """Trois états sont transmis jusqu'au front : réussi, échoué, inconnu."""
    client = build_client(
        sessions=[session("s1")],
        tool_calls=[tool_call("s1", is_error=None)],
    )

    events = client.get("/api/v1/sessions/s1").json()["events"]

    assert events[0]["is_error"] is None


def test_une_session_inconnue_repond_404_avec_une_explication() -> None:
    client = build_client(sessions=[session("s1")])

    response = client.get("/api/v1/sessions/inconnue-42")

    assert response.status_code == 404
    assert "inconnue-42" in response.json()["detail"]
