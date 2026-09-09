"""Objets de provenance des données de trace."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Provenance:
    """Origine d'une donnée importée."""

    source: str
    filename: str
    import_id: UUID | None = None
