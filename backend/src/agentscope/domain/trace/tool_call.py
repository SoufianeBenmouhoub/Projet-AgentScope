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

    is_error: bool | None = None
    """Issue de l'appel, en **trois** états.

    `True` échec, `False` réussite, `None` **on ne sait pas** — la source ne publie pas
    l'information. Le taux d'erreur exclut ce dernier cas de son dénominateur : l'assimiler
    à une réussite sous-estimerait systématiquement le taux d'échec.

    Distinct de `error`, qui porte un message quand il y en a un : un appel peut avoir
    échoué sans que la source explique pourquoi.
    """
