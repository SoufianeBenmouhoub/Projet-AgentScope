"""Port de normalisation des enregistrements bruts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
)


@dataclass(frozen=True)
class NormalizationIssue:
    """Anomalie rencontrée pendant la normalisation d'un enregistrement."""

    field: str
    message: str


@dataclass(frozen=True)
class NormalizedRecord:
    """Résultat de normalisation d'un enregistrement brut."""

    sessions: Sequence[SessionRecord]
    model_calls: Sequence[ModelCallRecord]
    tool_calls: Sequence[ToolCallRecord]
    issues: Sequence[NormalizationIssue]


class RecordNormalizerPort(ABC):
    """Contrat de transformation des données brutes vers le modèle commun."""

    @abstractmethod
    def normalize(
        self,
        record: dict[str, Any],
        mapping: dict[str, str | None],
        source: str,
    ) -> NormalizedRecord:
        """Normalise un enregistrement brut selon un mapping validé."""
        ...
