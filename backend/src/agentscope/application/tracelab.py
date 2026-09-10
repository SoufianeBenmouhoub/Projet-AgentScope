"""Préréglage de mapping pour les exports JSONL de TraceLab.

TraceLab publie une invocation de modèle par ligne ; ses appels d'outils et ses
horodatages sont imbriqués. Ce mapping permet donc de l'importer avec le moteur générique
sans lui ajouter de connaissance spécifique de TraceLab.
"""

from __future__ import annotations

TRACELAB_MAPPING: dict[str, str | None] = {
    "session_id": "session_id",
    "agent": "provider",
    "session_status": None,
    "occurred_at": "timing_events[0].timestamp",
    "ended_at": None,
    "model": "model",
    "input_tokens": "input_tokens_total",
    "output_tokens": "output_tokens",
    "cache_creation_tokens": "claude_cache_creation_input_tokens",
    "model_call_id": "round_id",
    "tools": "tools",
    "tool_name": "tool_name",
    "tool_started_at": "emitted_at",
    "tool_ended_at": "result_at",
    "tool_is_error": "is_error",
    "tool_error": None,
    "tool_call_id": "tool_call_id",
}


def mapping_for_source(source_name: str) -> dict[str, str | None] | None:
    """Retourne une copie du préréglage quand la source est un export TraceLab."""
    if source_name.strip().casefold().startswith("tracelab"):
        return dict(TRACELAB_MAPPING)
    return None
