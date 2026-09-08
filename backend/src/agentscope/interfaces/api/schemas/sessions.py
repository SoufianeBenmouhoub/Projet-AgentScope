"""Schémas de sortie de la vue détaillée d'une session."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from agentscope.domain.metrics.session_detail import SessionDetail, SessionEvent
from agentscope.domain.metrics.session_list import SessionList, SessionSummary
from agentscope.interfaces.api.schemas.metrics import AggregateResponse


class SessionSummaryResponse(BaseModel):
    """Une session vue de loin, telle qu'elle apparaît dans une liste."""

    session_id: str
    source: str
    agent: str
    started_at: datetime | None
    ended_at: datetime | None
    duration: AggregateResponse
    model_calls: int
    tool_calls: int
    input_tokens: AggregateResponse

    @classmethod
    def from_domain(cls, summary: SessionSummary) -> SessionSummaryResponse:
        return cls(
            session_id=summary.session_id,
            source=summary.source,
            agent=summary.agent,
            started_at=summary.started_at,
            ended_at=summary.ended_at,
            duration=AggregateResponse.from_domain(summary.duration),
            model_calls=summary.model_calls,
            tool_calls=summary.tool_calls,
            input_tokens=AggregateResponse.from_domain(summary.input_tokens),
        )


class SessionListResponse(BaseModel):
    sessions: list[SessionSummaryResponse]
    total: int = Field(
        description="Nombre de sessions du périmètre, y compris celles que la liste ne montre pas."
    )
    truncated: bool

    @classmethod
    def from_domain(cls, listing: SessionList) -> SessionListResponse:
        return cls(
            sessions=[SessionSummaryResponse.from_domain(item) for item in listing.sessions],
            total=listing.total,
            truncated=listing.is_truncated,
        )


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
