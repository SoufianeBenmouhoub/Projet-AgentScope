"""Tests de la vue détaillée d'une session."""

from __future__ import annotations

import pytest

from agentscope.application.use_cases.get_session_detail import (
    GetSessionDetail,
    SessionNotFound,
)
from agentscope.domain.metrics.session_detail import SessionEventKind
from tests.application.builders import model_call, session, tool_call
from tests.fakes.trace_read import InMemoryTraceRead


def _detail(session_id: str = "s1", **records):
    return GetSessionDetail(InMemoryTraceRead(**records)).execute(session_id)


def test_assemble_la_chronologie_des_appels_de_la_session() -> None:
    detail = _detail(
        sessions=[session("s1")],
        model_calls=[model_call("s1"), model_call("s1")],
        tool_calls=[tool_call("s1", tool_name="bash")],
    )

    assert detail.model_calls == 2
    assert detail.tool_calls == 1
    assert len(detail.events) == 3
    assert {event.kind for event in detail.events} == {
        SessionEventKind.MODEL_CALL,
        SessionEventKind.TOOL_CALL,
    }


def test_nexpose_que_les_enregistrements_de_la_session_demandee() -> None:
    detail = _detail(
        "s1",
        sessions=[session("s1"), session("s2")],
        model_calls=[model_call("s1"), model_call("s2"), model_call("s2")],
    )

    assert detail.session_id == "s1"
    assert detail.model_calls == 1


def test_les_evenements_sont_ordonnes_chronologiquement() -> None:
    detail = _detail(
        sessions=[session("s1")],
        model_calls=[model_call("s1", day=3)],
        tool_calls=[tool_call("s1", day=1), tool_call("s1", day=2)],
    )

    moments = [event.occurred_at for event in detail.events]

    assert moments == sorted(moments)


def test_les_evenements_non_dates_sont_conserves_en_fin_de_chronologie() -> None:
    """Les retirer masquerait un défaut de la trace : ils restent, mais à la fin."""
    detail = _detail(
        sessions=[session("s1")],
        tool_calls=[tool_call("s1", dated=False), tool_call("s1", day=1)],
    )

    assert len(detail.events) == 2
    assert detail.events[0].occurred_at is not None
    assert detail.events[-1].occurred_at is None


def test_la_duree_est_calculee_a_partir_des_bornes_de_la_session() -> None:
    detail = _detail(sessions=[session("s1", duration_minutes=15)])

    assert detail.duration.value == 15 * 60
    assert detail.duration.is_available is True


def test_une_session_sans_horodatage_a_une_duree_indisponible_et_non_nulle() -> None:
    detail = _detail(sessions=[session("s1", dated=False)])

    assert detail.duration.value is None
    assert detail.duration.is_available is False


def test_les_tokens_de_la_session_ignorent_les_appels_sans_compteur() -> None:
    detail = _detail(
        sessions=[session("s1")],
        model_calls=[
            model_call("s1", input_tokens=100),
            model_call("s1", input_tokens=None),
        ],
    )

    assert detail.input_tokens.value == 100
    assert detail.input_tokens.covered == 1
    assert detail.input_tokens.total == 2


def test_compte_les_appels_doutils_en_erreur() -> None:
    detail = _detail(
        sessions=[session("s1")],
        tool_calls=[
            tool_call("s1", is_error=True),
            tool_call("s1", is_error=False),
            tool_call("s1", is_error=None),
        ],
    )

    assert detail.failed_tool_calls == 1


def test_une_session_inconnue_est_refusee_avec_une_explication() -> None:
    with pytest.raises(SessionNotFound, match="inconnue-42"):
        _detail("inconnue-42", sessions=[session("s1")])
