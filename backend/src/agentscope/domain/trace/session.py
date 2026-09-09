"""Entité métier représentant une session de trace."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from agentscope.domain.trace.provenance import Provenance


@dataclass(frozen=True)
class Session:
    """Session complète d'utilisation d'un agent."""

    id: UUID
    external_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    agent_name: str | None
    status: str | None
    provenance: Provenance
