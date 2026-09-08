"""Schémas de sortie de la vue détaillée d'une session."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from agentscope.domain.metrics.session_detail import SessionDetail, SessionEvent
from agentscope.interfaces.api.schemas.metrics import AggregateResponse


class SessionEventResponse(BaseModel):
    kind: str = Field(description="« model_call » ou « tool_call ».")
    label: str
    occurred_at: datetime | None = Field(
        description="Null quand la trace ne date pas l'événement. Ces événements sont "
        "conservés en fin de chronologie plutôt que supprimés."
    )
    input_tokens: int | None
    is_error: bool | None = Field(
        description="Null quand la source ne publie pas l'issue de l'appel — un troisième "
        "état, distinct de réussi et d'échoué."
    )
    latency_ms: int | None

    @classmethod
    def from_domain(cls, event: SessionEvent) -> SessionEventResponse:
        return cls(
            kind=event.kind.value,
            label=event.label,
            occurred_at=event.occurred_at,
            input_tokens=event.input_tokens,
            is_error=event.is_error,
            latency_ms=event.latency_ms,
        )


class SessionDetailResponse(BaseModel):
    session_id: str
    source: str
    agent: str
    started_at: datetime | None
    ended_at: datetime | None
    duration: AggregateResponse = Field(
        description="Durée de la session. Indisponible — et non nulle — quand les "
        "horodatages manquent."
    )
    input_tokens: AggregateResponse
    model_calls: int
    tool_calls: int
    failed_tool_calls: int
    events: list[SessionEventResponse]

    @classmethod
    def from_domain(cls, detail: SessionDetail) -> SessionDetailResponse:
        return cls(
            session_id=detail.session_id,
            source=detail.source,
            agent=detail.agent,
            started_at=detail.started_at,
            ended_at=detail.ended_at,
            duration=AggregateResponse.from_domain(detail.duration),
            input_tokens=AggregateResponse.from_domain(detail.input_tokens),
            model_calls=detail.model_calls,
            tool_calls=detail.tool_calls,
            failed_tool_calls=detail.failed_tool_calls,
            events=[SessionEventResponse.from_domain(event) for event in detail.events],
        )
