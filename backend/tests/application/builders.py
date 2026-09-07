"""Constructeurs d'enregistrements pour les tests.

Des valeurs par défaut cohérentes, pour que chaque test ne montre que ce qu'il teste.
`dated=False` produit un enregistrement sans horodatage — le cas qui distingue un
traitement honnête des valeurs manquantes d'un traitement complaisant.
"""

from __future__ import annotations

from datetime import datetime

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
)

CLAUDE = "tracelab-claude"
CODEX = "tracelab-codex"


def _agent_of(source: str) -> str:
    return "claude-code" if source == CLAUDE else "codex"


def session(
    session_id: str,
    source: str = CLAUDE,
    day: int = 1,
    dated: bool = True,
    duration_minutes: int = 30,
) -> SessionRecord:
    started_at = datetime(2026, 9, day, 10, 0) if dated else None
    ended_at = datetime(2026, 9, day, 10, duration_minutes) if dated else None
    return SessionRecord(
        session_id=session_id,
        source=source,
        agent=_agent_of(source),
        started_at=started_at,
        ended_at=ended_at,
    )


def model_call(
    session_id: str,
    source: str = CLAUDE,
    day: int = 1,
    dated: bool = True,
    input_tokens: int | None = 100,
    cache_creation_tokens: int | None = None,
    model: str | None = "claude-opus-5",
) -> ModelCallRecord:
    return ModelCallRecord(
        session_id=session_id,
        source=source,
        agent=_agent_of(source),
        model=model,
        occurred_at=datetime(2026, 9, day, 10, 5) if dated else None,
        input_tokens=input_tokens,
        output_tokens=None,
        cache_creation_tokens=cache_creation_tokens,
    )


def tool_call(
    session_id: str,
    source: str = CLAUDE,
    day: int = 1,
    dated: bool = True,
    tool_name: str = "read_file",
    is_error: bool | None = False,
    latency_ms: int | None = 100,
) -> ToolCallRecord:
    return ToolCallRecord(
        session_id=session_id,
        source=source,
        tool_name=tool_name,
        occurred_at=datetime(2026, 9, day, 10, 6) if dated else None,
        is_error=is_error,
        latency_ms=latency_ms,
    )
