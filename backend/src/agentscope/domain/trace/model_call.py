"""Entité métier représentant un appel à un modèle IA."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from agentscope.domain.trace.provenance import Provenance


@dataclass(frozen=True)
class ModelCall:
    """Appel individuel à un modèle IA pendant une session."""

    id: UUID
    session_id: UUID
    external_id: str | None
    model_name: str | None
    started_at: datetime | None
    ended_at: datetime | None
    input_tokens: int | None
    output_tokens: int | None
    cached_tokens: int | None
    status: str | None
    provenance: Provenance
