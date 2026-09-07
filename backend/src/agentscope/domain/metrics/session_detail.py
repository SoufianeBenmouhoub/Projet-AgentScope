"""Vue détaillée d'une session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from agentscope.domain.metrics.aggregation import Aggregate


class SessionEventKind(Enum):
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"


@dataclass(frozen=True)
class SessionEvent:
    """Un événement de la chronologie : une invocation du modèle ou un appel d'outil."""

    kind: SessionEventKind
    label: str
    occurred_at: datetime | None
    input_tokens: int | None
    is_error: bool | None
    latency_ms: int | None


@dataclass(frozen=True)
class SessionDetail:
    """Une session et sa chronologie.

    `duration` est un agrégat et non un nombre : une session dont les horodatages ne sont
    pas renseignés a une durée **indisponible**, pas une durée nulle.
    """

    session_id: str
    source: str
    agent: str
    started_at: datetime | None
    ended_at: datetime | None
    duration: Aggregate
    input_tokens: Aggregate
    model_calls: int
    tool_calls: int
    events: tuple[SessionEvent, ...]

    @property
    def failed_tool_calls(self) -> int:
        return sum(
            1
            for event in self.events
            if event.kind is SessionEventKind.TOOL_CALL and event.is_error
        )
