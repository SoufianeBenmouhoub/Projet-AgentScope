"""Série d'activité journalière sur le périmètre filtré."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta

from agentscope.application.ports.trace_read import TraceFilter, TraceReadPort
from agentscope.domain.metrics.activity import ActivityPoint, ActivitySeries


class GetActivitySeries:
    """Produit une série journalière continue, sans trou artificiel.

    Deux règles, toutes deux issues du même principe — ne pas faire mentir le graphique :

    - une journée sans activité **à l'intérieur** de la période vaut zéro, et apparaît
      comme telle : la retirer donnerait une courbe qui saute par-dessus les jours creux ;
    - un enregistrement sans horodatage n'appartient à aucune journée. Il n'est pas jeté en
      silence : il est compté à part, pour que l'interface puisse signaler l'écart entre
      ce que la courbe montre et ce que le périmètre contient.
    """

    def __init__(self, traces: TraceReadPort) -> None:
        self._traces = traces

    def execute(self, filters: TraceFilter) -> ActivitySeries:
        sessions = self._traces.sessions(filters)
        model_calls = self._traces.model_calls(filters)
        tool_calls = self._traces.tool_calls(filters)

        sessions_by_day: dict[date, set[str]] = defaultdict(set)
        for session in sessions:
            if session.started_at is not None:
                sessions_by_day[session.started_at.date()].add(session.session_id)

        model_calls_by_day: dict[date, int] = defaultdict(int)
        for call in model_calls:
            if call.occurred_at is not None:
                model_calls_by_day[call.occurred_at.date()] += 1

        tool_calls_by_day: dict[date, int] = defaultdict(int)
        for call in tool_calls:
            if call.occurred_at is not None:
                tool_calls_by_day[call.occurred_at.date()] += 1

        observed = set(sessions_by_day) | set(model_calls_by_day) | set(tool_calls_by_day)
        days = _days_to_cover(observed, filters)

        points = tuple(
            ActivityPoint(
                day=day,
                sessions=len(sessions_by_day.get(day, ())),
                model_calls=model_calls_by_day.get(day, 0),
                tool_calls=tool_calls_by_day.get(day, 0),
                session_ids=tuple(sorted(sessions_by_day.get(day, ()))),
            )
            for day in days
        )

        return ActivitySeries(
            points=points,
            undated_sessions=_undated(session.started_at for session in sessions),
            undated_model_calls=_undated(call.occurred_at for call in model_calls),
            undated_tool_calls=_undated(call.occurred_at for call in tool_calls),
        )


def _undated(moments) -> int:
    return sum(1 for moment in moments if moment is None)


def _days_to_cover(observed: set[date], filters: TraceFilter) -> Sequence[date]:
    """Journées à représenter, bornes du filtre prioritaires sur les données observées.

    Quand l'utilisateur demande une période, la série la couvre entièrement — y compris
    ses extrémités vides, qui sont une information : il ne s'est rien passé ce jour-là.
    """
    first = filters.since or (min(observed) if observed else None)
    last = filters.until or (max(observed) if observed else None)

    if first is None or last is None or first > last:
        return ()

    span = (last - first).days
    return [first + timedelta(days=offset) for offset in range(span + 1)]
