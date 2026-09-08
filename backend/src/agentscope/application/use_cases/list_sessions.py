"""Liste des sessions d'un périmètre filtré."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFilter,
    TraceReadPort,
)
from agentscope.domain.metrics.aggregation import sum_of
from agentscope.domain.metrics.session_detail import duration_between
from agentscope.domain.metrics.session_list import SessionList, SessionSummary

#: Plafond d'affichage. Au-delà, l'utilisateur affine son filtre plutôt que de faire
#: défiler : c'est à ça que servent les filtres.
MAX_SESSIONS = 100


class ListSessions:
    """Les sessions du périmètre, de la plus récente à la plus ancienne.

    Les sessions sans horodatage passent en fin de liste plutôt que d'être exclues : leur
    absence de date est un défaut de la trace, pas une raison de les faire disparaître.
    """

    def __init__(self, traces: TraceReadPort) -> None:
        self._traces = traces

    def execute(self, filters: TraceFilter) -> SessionList:
        sessions = self._traces.sessions(filters)
        model_calls = _by_session(self._traces.model_calls(filters))
        tool_calls = _by_session(self._traces.tool_calls(filters))

        summaries = [
            _summarize(session, model_calls[session.session_id], tool_calls[session.session_id])
            for session in sessions
        ]
        summaries.sort(key=_most_recent_first)

        return SessionList(sessions=tuple(summaries[:MAX_SESSIONS]), total=len(summaries))


def _by_session(records: Sequence) -> dict[str, list]:
    grouped: dict[str, list] = defaultdict(list)
    for record in records:
        grouped[record.session_id].append(record)
    return grouped


def _summarize(
    session: SessionRecord,
    model_calls: Sequence[ModelCallRecord],
    tool_calls: Sequence[ToolCallRecord],
) -> SessionSummary:
    return SessionSummary(
        session_id=session.session_id,
        source=session.source,
        agent=session.agent,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration=duration_between(session.started_at, session.ended_at),
        model_calls=len(model_calls),
        tool_calls=len(tool_calls),
        input_tokens=sum_of([call.input_tokens for call in model_calls], "tokens"),
    )


def _most_recent_first(summary: SessionSummary) -> tuple[int, float, str]:
    """Les plus récentes d'abord ; celles sans date en fin de liste, mais présentes."""
    if summary.started_at is None:
        return (1, 0.0, summary.session_id)
    return (0, -summary.started_at.timestamp(), summary.session_id)
