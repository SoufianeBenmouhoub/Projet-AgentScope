"""Tests de la synthèse d'indicateurs, contre une doublure en mémoire.

Aucune base, aucun serveur : ce sont les règles de calcul qui sont vérifiées, pas le
stockage. C'est la condition posée par l'énoncé pour que ces règles survivent à un
changement d'interface ou de base.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFilter,
)
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.domain.metrics.catalog import IndicatorValue
from tests.fakes.trace_read import InMemoryTraceRead

CLAUDE = "tracelab-claude"
CODEX = "tracelab-codex"


def _session(session_id: str, source: str = CLAUDE, day: int = 1) -> SessionRecord:
    return SessionRecord(
        session_id=session_id,
        source=source,
        agent="claude-code" if source == CLAUDE else "codex",
        started_at=datetime(2026, 9, day, 10, 0),
        ended_at=datetime(2026, 9, day, 10, 30),
    )


def _model_call(
    session_id: str,
    source: str = CLAUDE,
    day: int = 1,
    input_tokens: int | None = 100,
    cache_creation_tokens: int | None = None,
    model: str | None = "claude-opus-5",
) -> ModelCallRecord:
    return ModelCallRecord(
        session_id=session_id,
        source=source,
        agent="claude-code" if source == CLAUDE else "codex",
        model=model,
        occurred_at=datetime(2026, 9, day, 10, 5),
        input_tokens=input_tokens,
        output_tokens=None,
        cache_creation_tokens=cache_creation_tokens,
    )


def _tool_call(
    session_id: str,
    source: str = CLAUDE,
    day: int = 1,
    is_error: bool | None = False,
    latency_ms: int | None = 100,
    tool_name: str = "read_file",
) -> ToolCallRecord:
    return ToolCallRecord(
        session_id=session_id,
        source=source,
        tool_name=tool_name,
        occurred_at=datetime(2026, 9, day, 10, 6),
        is_error=is_error,
        latency_ms=latency_ms,
    )


def _by_key(values: tuple[IndicatorValue, ...]) -> dict[str, IndicatorValue]:
    return {value.definition.key: value for value in values}


def test_chaque_indicateur_est_livre_avec_sa_definition() -> None:
    """Un chiffre sans définition n'est pas publiable : l'énoncé l'exige."""
    use_case = GetKpiSummary(InMemoryTraceRead(sessions=[_session("s1")]))

    for indicator in use_case.execute(TraceFilter()):
        assert indicator.definition.computation
        assert indicator.definition.unit
        assert indicator.definition.scope
        assert indicator.definition.missing_values


def test_denombre_les_sessions_et_les_appels_au_modele() -> None:
    use_case = GetKpiSummary(
        InMemoryTraceRead(
            sessions=[_session("s1"), _session("s2")],
            model_calls=[_model_call("s1"), _model_call("s1"), _model_call("s2")],
        )
    )

    indicators = _by_key(use_case.execute(TraceFilter()))

    assert indicators["sessions_total"].aggregate.value == 2
    assert indicators["model_calls_total"].aggregate.value == 3


def test_somme_les_tokens_en_entree_en_ignorant_les_appels_sans_compteur() -> None:
    use_case = GetKpiSummary(
        InMemoryTraceRead(
            model_calls=[
                _model_call("s1", input_tokens=100),
                _model_call("s1", input_tokens=None),
                _model_call("s1", input_tokens=300),
            ]
        )
    )

    tokens = _by_key(use_case.execute(TraceFilter()))["input_tokens_total"].aggregate

    assert tokens.value == 400
    assert tokens.covered == 2
    assert tokens.total == 3
    assert tokens.is_partial is True


def test_un_compteur_publie_par_aucune_source_reste_indisponible() -> None:
    """Le cas réel : le cache n'est publié que par certains agents. Ce n'est pas zéro."""
    use_case = GetKpiSummary(
        InMemoryTraceRead(
            model_calls=[
                _model_call("s1", source=CODEX, cache_creation_tokens=None),
                _model_call("s2", source=CODEX, cache_creation_tokens=None),
            ]
        )
    )

    cache = _by_key(use_case.execute(TraceFilter()))["cache_creation_tokens"].aggregate

    assert cache.value is None
    assert cache.is_available is False


def test_un_indicateur_propre_a_une_source_est_signale_quand_on_melange_les_sources() -> None:
    use_case = GetKpiSummary(
        InMemoryTraceRead(
            model_calls=[
                _model_call("s1", source=CLAUDE, cache_creation_tokens=500),
                _model_call("s2", source=CODEX, cache_creation_tokens=None),
            ]
        )
    )

    indicators = _by_key(use_case.execute(TraceFilter()))

    assert indicators["cache_creation_tokens"].mixes_incomparable_sources is True
    assert indicators["input_tokens_total"].mixes_incomparable_sources is False


def test_le_taux_derreur_exclut_les_appels_dont_lissue_est_inconnue() -> None:
    use_case = GetKpiSummary(
        InMemoryTraceRead(
            tool_calls=[
                _tool_call("s1", is_error=True),
                _tool_call("s1", is_error=False),
                _tool_call("s1", is_error=False),
                _tool_call("s1", is_error=False),
                _tool_call("s1", is_error=None),
                _tool_call("s1", is_error=None),
            ]
        )
    )

    rate = _by_key(use_case.execute(TraceFilter()))["tool_error_rate"].aggregate

    assert rate.value == 25.0  # 1 erreur sur 4 appels observés, pas sur 6
    assert rate.covered == 4
    assert rate.total == 6


def test_la_latence_mediane_ignore_les_appels_sans_duree_mesuree() -> None:
    use_case = GetKpiSummary(
        InMemoryTraceRead(
            tool_calls=[
                _tool_call("s1", latency_ms=10),
                _tool_call("s1", latency_ms=None),
                _tool_call("s1", latency_ms=30),
                _tool_call("s1", latency_ms=20),
            ]
        )
    )

    latency = _by_key(use_case.execute(TraceFilter()))["tool_latency_median"].aggregate

    assert latency.value == 20
    assert latency.covered == 3


class TestFiltrage:
    """Un indicateur doit rester correct après filtrage — exigence explicite de l'énoncé."""

    def _use_case(self) -> GetKpiSummary:
        return GetKpiSummary(
            InMemoryTraceRead(
                sessions=[
                    _session("s1", source=CLAUDE, day=1),
                    _session("s2", source=CODEX, day=5),
                ],
                model_calls=[
                    _model_call("s1", source=CLAUDE, day=1, input_tokens=100),
                    _model_call("s2", source=CODEX, day=5, input_tokens=700),
                ],
            )
        )

    def test_sans_filtre_le_total_couvre_tout(self) -> None:
        indicators = _by_key(self._use_case().execute(TraceFilter()))

        assert indicators["sessions_total"].aggregate.value == 2
        assert indicators["input_tokens_total"].aggregate.value == 800

    def test_le_filtre_par_source_restreint_le_perimetre(self) -> None:
        indicators = _by_key(self._use_case().execute(TraceFilter(sources=(CLAUDE,))))

        assert indicators["sessions_total"].aggregate.value == 1
        assert indicators["input_tokens_total"].aggregate.value == 100

    def test_le_filtre_par_periode_restreint_le_perimetre(self) -> None:
        filters = TraceFilter(since=date(2026, 9, 4), until=date(2026, 9, 6))

        indicators = _by_key(self._use_case().execute(filters))

        assert indicators["sessions_total"].aggregate.value == 1
        assert indicators["input_tokens_total"].aggregate.value == 700

    def test_le_cumul_des_perimetres_filtres_egale_le_total(self) -> None:
        """La propriété qui attrape les erreurs de jointure : la somme des parties = le tout."""
        use_case = self._use_case()

        claude = _by_key(use_case.execute(TraceFilter(sources=(CLAUDE,))))
        codex = _by_key(use_case.execute(TraceFilter(sources=(CODEX,))))
        both = _by_key(use_case.execute(TraceFilter()))

        assert (
            claude["input_tokens_total"].aggregate.value
            + codex["input_tokens_total"].aggregate.value
            == both["input_tokens_total"].aggregate.value
        )

    def test_un_filtre_aux_bornes_inversees_est_refuse(self) -> None:
        with pytest.raises(ValueError, match="postérieure"):
            TraceFilter(since=date(2026, 9, 10), until=date(2026, 9, 1))
