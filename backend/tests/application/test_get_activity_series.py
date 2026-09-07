"""Tests de la série d'activité journalière."""

from __future__ import annotations

from datetime import date

from agentscope.application.ports.trace_read import TraceFilter
from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from tests.application.builders import model_call, session, tool_call
from tests.fakes.trace_read import InMemoryTraceRead


def _series(filters: TraceFilter | None = None, **records):
    use_case = GetActivitySeries(InMemoryTraceRead(**records))
    return use_case.execute(filters or TraceFilter())


def test_regroupe_lactivite_par_journee() -> None:
    result = _series(
        sessions=[session("s1", day=1), session("s2", day=1), session("s3", day=2)],
        model_calls=[model_call("s1", day=1), model_call("s3", day=2)],
        tool_calls=[tool_call("s1", day=1)],
    )

    assert [point.day for point in result.points] == [date(2026, 9, 1), date(2026, 9, 2)]
    assert result.points[0].sessions == 2
    assert result.points[0].model_calls == 1
    assert result.points[0].tool_calls == 1
    assert result.points[1].sessions == 1


def test_une_journee_creuse_au_milieu_vaut_zero_et_reste_dans_la_serie() -> None:
    """Retirer les jours vides donnerait une courbe qui saute par-dessus les creux."""
    result = _series(sessions=[session("s1", day=1), session("s2", day=4)])

    assert [point.day.day for point in result.points] == [1, 2, 3, 4]
    assert result.points[1].sessions == 0
    assert result.points[2].sessions == 0


def test_les_bornes_du_filtre_priment_sur_les_donnees_observees() -> None:
    filters = TraceFilter(since=date(2026, 9, 1), until=date(2026, 9, 5))

    result = _series(filters, sessions=[session("s1", day=3)])

    assert len(result.points) == 5
    assert result.points[0].sessions == 0
    assert result.points[2].sessions == 1
    assert result.points[4].sessions == 0


def test_les_enregistrements_sans_horodatage_sont_comptes_a_part_et_non_jetes() -> None:
    """Les supprimer en silence ferait mentir le graphique sur son exhaustivité."""
    result = _series(
        sessions=[session("s1", day=1), session("s2", dated=False)],
        model_calls=[model_call("s2", dated=False), model_call("s2", dated=False)],
        tool_calls=[tool_call("s2", dated=False)],
    )

    assert result.undated_sessions == 1
    assert result.undated_model_calls == 2
    assert result.undated_tool_calls == 1
    assert result.has_undated_records is True
    assert sum(point.sessions for point in result.points) == 1


def test_une_serie_entierement_datee_ne_signale_aucun_ecart() -> None:
    result = _series(sessions=[session("s1", day=1)])

    assert result.has_undated_records is False


def test_chaque_point_porte_les_sessions_de_la_journee() -> None:
    """C'est ce qui permet de cliquer sur un point et de retrouver les sessions."""
    result = _series(sessions=[session("s2", day=1), session("s1", day=1)])

    assert result.points[0].session_ids == ("s1", "s2")


def test_un_perimetre_vide_donne_une_serie_vide() -> None:
    result = _series()

    assert result.points == ()
    assert result.has_undated_records is False


def test_un_perimetre_sans_aucun_horodatage_ne_produit_aucun_point() -> None:
    result = _series(sessions=[session("s1", dated=False)])

    assert result.points == ()
    assert result.undated_sessions == 1
