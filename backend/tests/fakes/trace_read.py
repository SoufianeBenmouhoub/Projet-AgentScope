"""Doublure en mémoire du port de lecture des traces.

C'est elle qui permet au lot 5 d'avancer avant que le stockage réel n'existe, et qui rend
les tests d'indicateurs instantanés. Le filtrage y est volontairement naïf : ce qui est
testé ici, ce sont les règles de calcul, pas une implémentation de requêtes.
"""

from __future__ import annotations

from collections.abc import Sequence

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFilter,
    TraceReadPort,
)


class InMemoryTraceRead(TraceReadPort):
    def __init__(
        self,
        *,
        sessions: Sequence[SessionRecord] = (),
        model_calls: Sequence[ModelCallRecord] = (),
        tool_calls: Sequence[ToolCallRecord] = (),
    ) -> None:
        self._sessions = tuple(sessions)
        self._model_calls = tuple(model_calls)
        self._tool_calls = tuple(tool_calls)

    def sessions(self, filters: TraceFilter) -> Sequence[SessionRecord]:
        return tuple(
            record
            for record in self._sessions
            if _matches_source(record.source, filters)
            and _matches_agent(record.agent, filters)
            and _matches_period(record.started_at, filters)
        )

    def model_calls(self, filters: TraceFilter) -> Sequence[ModelCallRecord]:
        return tuple(
            record
            for record in self._model_calls
            if _matches_source(record.source, filters)
            and _matches_agent(record.agent, filters)
            and _matches_model(record.model, filters)
            and _matches_period(record.occurred_at, filters)
        )

    def tool_calls(self, filters: TraceFilter) -> Sequence[ToolCallRecord]:
        return tuple(
            record
            for record in self._tool_calls
            if _matches_source(record.source, filters)
            and _matches_period(record.occurred_at, filters)
        )


def _matches_source(source: str, filters: TraceFilter) -> bool:
    return not filters.sources or source in filters.sources


def _matches_agent(agent: str, filters: TraceFilter) -> bool:
    return not filters.agents or agent in filters.agents


def _matches_model(model: str | None, filters: TraceFilter) -> bool:
    return not filters.models or (model is not None and model in filters.models)


def _matches_period(moment, filters: TraceFilter) -> bool:
    """Un enregistrement sans horodatage n'est retenu que si aucune période n'est demandée.

    L'exclure d'un filtre par période est le comportement honnête : on ne sait pas s'il y
    appartient, donc on ne l'y compte pas — mais l'écart doit rester visible ailleurs, via
    l'indicateur de qualité des données.
    """
    if filters.since is None and filters.until is None:
        return True
    if moment is None:
        return False

    day = moment.date()
    after_start = filters.since is None or day >= filters.since
    before_end = filters.until is None or day <= filters.until
    return after_start and before_end
