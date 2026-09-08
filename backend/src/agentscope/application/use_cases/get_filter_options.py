"""Valeurs disponibles pour les filtres du dashboard."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import date, datetime

from agentscope.application.ports.trace_read import TraceFilter, TraceReadPort
from agentscope.domain.metrics.filter_options import FilterOptions


class GetFilterOptions:
    """Dérive les choix de filtre des traces réellement importées.

    Les options sont calculées sur **l'ensemble des traces**, sans tenir compte des filtres
    déjà actifs. Les restreindre progressivement paraît élégant mais fait disparaître de la
    liste une valeur que l'utilisateur vient de sélectionner, ce qui rend l'interface
    imprévisible.

    Ce cas d'utilisation n'a demandé aucune extension du port : les enregistrements exposés
    portent déjà tout ce qu'il faut.
    """

    def __init__(self, traces: TraceReadPort) -> None:
        self._traces = traces

    def execute(self) -> FilterOptions:
        everything = TraceFilter()
        sessions = self._traces.sessions(everything)
        model_calls = self._traces.model_calls(everything)
        tool_calls = self._traces.tool_calls(everything)

        sources = _sorted_values(
            [record.source for record in sessions]
            + [record.source for record in model_calls]
            + [record.source for record in tool_calls]
        )
        agents = _sorted_values(
            [record.agent for record in sessions] + [record.agent for record in model_calls]
        )
        models = _sorted_values([record.model for record in model_calls])

        days = list(
            _days(
                [record.started_at for record in sessions]
                + [record.ended_at for record in sessions]
                + [record.occurred_at for record in model_calls]
                + [record.occurred_at for record in tool_calls]
            )
        )

        return FilterOptions(
            sources=sources,
            agents=agents,
            models=models,
            first_day=min(days) if days else None,
            last_day=max(days) if days else None,
        )


def _sorted_values(values: Iterable[str | None]) -> tuple[str, ...]:
    """Valeurs distinctes, triées, sans les absences ni les chaînes vides."""
    return tuple(sorted({value for value in values if value}))


def _days(moments: Iterable[datetime | None]) -> Iterator[date]:
    for moment in moments:
        if moment is not None:
            yield moment.date()
