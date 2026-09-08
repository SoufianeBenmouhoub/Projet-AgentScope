"""Tests de la liste des sessions d'un périmètre."""

from __future__ import annotations

import pytest

from agentscope.application.ports.trace_read import TraceFilter
from agentscope.application.use_cases.list_sessions import MAX_SESSIONS, ListSessions
from agentscope.domain.metrics.session_list import SessionList
from tests.application.builders import CLAUDE, CODEX, model_call, session, tool_call
from tests.fakes.trace_read import InMemoryTraceRead


def _listing(filters: TraceFilter | None = None, **records) -> SessionList:
    return ListSessions(InMemoryTraceRead(**records)).execute(filters or TraceFilter())


def test_resume_chaque_session_avec_ses_appels() -> None:
    listing = _listing(
        sessions=[session("s1", duration_minutes=20)],
        model_calls=[model_call("s1", input_tokens=100), model_call("s1", input_tokens=200)],
        tool_calls=[tool_call("s1")],
    )

    summary = listing.sessions[0]

    assert summary.session_id == "s1"
    assert summary.model_calls == 2
    assert summary.tool_calls == 1
    assert summary.input_tokens.value == 300
    assert summary.duration.value == 20 * 60


def test_les_sessions_les_plus_recentes_dabord() -> None:
    listing = _listing(sessions=[session("ancienne", day=1), session("recente", day=5)])

    assert [item.session_id for item in listing.sessions] == ["recente", "ancienne"]


def test_les_sessions_sans_date_restent_dans_la_liste_mais_a_la_fin() -> None:
    """Leur absence de date est un défaut de la trace, pas une raison de les cacher."""
    listing = _listing(sessions=[session("sans-date", dated=False), session("datee", day=1)])

    assert [item.session_id for item in listing.sessions] == ["datee", "sans-date"]


def test_une_session_sans_horodatage_a_une_duree_indisponible_et_non_nulle() -> None:
    listing = _listing(sessions=[session("s1", dated=False)])

    assert listing.sessions[0].duration.value is None


def test_une_session_dont_aucun_appel_ne_compte_les_tokens_reste_indisponible() -> None:
    listing = _listing(
        sessions=[session("s1")],
        model_calls=[model_call("s1", input_tokens=None)],
    )

    assert listing.sessions[0].input_tokens.value is None


def test_le_filtre_par_identifiant_de_session_permet_le_retour_depuis_un_graphique() -> None:
    listing = _listing(
        TraceFilter(session_ids=("s2",)),
        sessions=[session("s1"), session("s2"), session("s3")],
    )

    assert [item.session_id for item in listing.sessions] == ["s2"]


def test_le_filtre_par_source_restreint_la_liste() -> None:
    listing = _listing(
        TraceFilter(sources=(CLAUDE,)),
        sessions=[session("s1", source=CLAUDE), session("s2", source=CODEX)],
    )

    assert [item.session_id for item in listing.sessions] == ["s1"]


def test_la_liste_est_plafonnee_mais_annonce_le_total_reel() -> None:
    """Une liste tronquée qui tairait le total ferait croire à un périmètre plus petit."""
    sessions = [session(f"s{index:03d}", day=1) for index in range(MAX_SESSIONS + 20)]

    listing = _listing(sessions=sessions)

    assert len(listing.sessions) == MAX_SESSIONS
    assert listing.total == MAX_SESSIONS + 20
    assert listing.is_truncated is True


def test_une_liste_complete_ne_se_declare_pas_tronquee() -> None:
    listing = _listing(sessions=[session("s1")])

    assert listing.is_truncated is False


def test_une_liste_qui_annonce_moins_que_ce_quelle_contient_est_refusee() -> None:
    with pytest.raises(ValueError, match="total annoncé"):
        SessionList(sessions=(), total=-1)
