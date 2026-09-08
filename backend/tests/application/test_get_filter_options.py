"""Tests des valeurs proposées par les filtres."""

from __future__ import annotations

from datetime import date

import pytest

from agentscope.application.use_cases.get_filter_options import GetFilterOptions
from agentscope.domain.metrics.filter_options import FilterOptions
from tests.application.builders import CLAUDE, CODEX, model_call, session, tool_call
from tests.fakes.trace_read import InMemoryTraceRead


def _options(**records) -> FilterOptions:
    return GetFilterOptions(InMemoryTraceRead(**records)).execute()


def test_liste_les_sources_les_agents_et_les_modeles_observes() -> None:
    options = _options(
        sessions=[session("s1", source=CLAUDE), session("s2", source=CODEX)],
        model_calls=[
            model_call("s1", source=CLAUDE, model="claude-opus-5"),
            model_call("s2", source=CODEX, model="gpt-x"),
        ],
    )

    assert options.sources == (CLAUDE, CODEX)
    assert options.agents == ("claude-code", "codex")
    assert options.models == ("claude-opus-5", "gpt-x")


def test_les_valeurs_sont_distinctes_et_triees() -> None:
    options = _options(
        model_calls=[
            model_call("s1", model="zeta"),
            model_call("s1", model="alpha"),
            model_call("s1", model="alpha"),
        ]
    )

    assert options.models == ("alpha", "zeta")


def test_une_valeur_non_renseignee_nest_pas_proposee_comme_choix() -> None:
    """On ne propose pas de filtrer sur « modèle inconnu » : ce n'est pas une valeur."""
    options = _options(
        model_calls=[model_call("s1", model="claude-opus-5"), model_call("s1", model=None)]
    )

    assert options.models == ("claude-opus-5",)


def test_borne_la_periode_sur_les_enregistrements_horodates() -> None:
    options = _options(
        sessions=[session("s1", day=3)],
        tool_calls=[tool_call("s1", day=9)],
    )

    assert options.first_day == date(2026, 9, 3)
    assert options.last_day == date(2026, 9, 9)


def test_sans_aucun_horodatage_la_periode_na_pas_de_bornes() -> None:
    options = _options(sessions=[session("s1", dated=False)])

    assert options.first_day is None
    assert options.last_day is None


def test_un_perimetre_vide_signale_quil_ny_a_rien_a_filtrer() -> None:
    options = _options()

    assert options.is_empty is True
    assert options.sources == ()


def test_des_bornes_incoherentes_sont_refusees() -> None:
    with pytest.raises(ValueError, match="postérieure"):
        FilterOptions(
            sources=(),
            agents=(),
            models=(),
            first_day=date(2026, 9, 10),
            last_day=date(2026, 9, 1),
        )
