"""Entité métier représentant un appel à un outil."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from agentscope.domain.trace.provenance import Provenance


@dataclass(frozen=True)
class ToolCall:
    """Appel individuel à un outil pendant une session."""

    id: UUID
    session_id: UUID
    external_id: str | None
    tool_name: str | None
    started_at: datetime | None
    ended_at: datetime | None
    status: str | None
    error: str | None
    provenance: Provenance
