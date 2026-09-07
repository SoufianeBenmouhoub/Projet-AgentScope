"""Vue détaillée d'une session."""

from __future__ import annotations

from datetime import datetime

from agentscope.application.ports.trace_read import TraceFilter, TraceReadPort
from agentscope.domain.metrics.aggregation import Aggregate, sum_of
from agentscope.domain.metrics.session_detail import (
    SessionDetail,
    SessionEvent,
    SessionEventKind,
)


class SessionNotFound(Exception):
    """Aucune session ne porte cet identifiant dans le périmètre consulté."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Aucune session « {session_id} » dans les traces importées.")
        self.session_id = session_id


class GetSessionDetail:
    """Assemble la chronologie d'une session à partir de ses appels.

    Le détail d'une session n'est qu'un périmètre restreint à une seule session : c'est le
    même filtre que celui du dashboard, donc le même chemin de lecture.
    """

    def __init__(self, traces: TraceReadPort) -> None:
        self._traces = traces

    def execute(self, session_id: str) -> SessionDetail:
        filters = TraceFilter(session_ids=(session_id,))

        sessions = self._traces.sessions(filters)
        if not sessions:
            raise SessionNotFound(session_id)
        session = sessions[0]

        model_calls = self._traces.model_calls(filters)
        tool_calls = self._traces.tool_calls(filters)

        events = [
            SessionEvent(
                kind=SessionEventKind.MODEL_CALL,
                label=call.model or "modèle non renseigné",
                occurred_at=call.occurred_at,
                input_tokens=call.input_tokens,
                is_error=None,
                latency_ms=None,
            )
            for call in model_calls
        ]
        events += [
            SessionEvent(
                kind=SessionEventKind.TOOL_CALL,
                label=call.tool_name,
                occurred_at=call.occurred_at,
                input_tokens=None,
                is_error=call.is_error,
                latency_ms=call.latency_ms,
            )
            for call in tool_calls
        ]

        return SessionDetail(
            session_id=session.session_id,
            source=session.source,
            agent=session.agent,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration=_duration(session.started_at, session.ended_at),
            input_tokens=sum_of([call.input_tokens for call in model_calls], "tokens"),
            model_calls=len(model_calls),
            tool_calls=len(tool_calls),
            events=tuple(sorted(events, key=_chronological)),
        )


def _chronological(event: SessionEvent) -> tuple[int, datetime]:
    """Trie par horodatage, les événements non datés rejetés en fin de chronologie.

    Ils ne sont pas retirés : leur présence est une information sur la qualité de la trace.
    """
    if event.occurred_at is None:
        return (1, datetime.max)
    return (0, event.occurred_at)


def _duration(started_at: datetime | None, ended_at: datetime | None) -> Aggregate:
    """Durée de la session, indisponible si les horodatages manquent.

    Une session dont on ne connaît pas les bornes n'a pas duré zéro seconde : on ne sait
    simplement pas combien de temps elle a duré.
    """
    if started_at is None or ended_at is None or ended_at < started_at:
        return Aggregate(value=None, unit="s", covered=0, total=1)
    return Aggregate(
        value=(ended_at - started_at).total_seconds(),
        unit="s",
        covered=1,
        total=1,
    )
