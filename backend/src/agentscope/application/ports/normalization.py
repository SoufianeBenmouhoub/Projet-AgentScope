"""Port de normalisation des enregistrements bruts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall


@dataclass(frozen=True)
class NormalizationIssue:
    """Anomalie rencontrée pendant la normalisation d'un enregistrement."""

    field: str
    message: str


@dataclass(frozen=True)
class NormalizedRecord:
    """Résultat de normalisation d'un enregistrement brut."""

    sessions: Sequence[Session]
    model_calls: Sequence[ModelCall]
    tool_calls: Sequence[ToolCall]
    issues: Sequence[NormalizationIssue]


class RecordNormalizerPort(ABC):
    """Contrat de transformation des données brutes vers le modèle métier."""

    @abstractmethod
    def normalize(
        self,
        record: dict[str, Any],
        mapping: dict[str, str | None],
        source: str,
        filename: str,
    ) -> NormalizedRecord:
        """Normalise un enregistrement brut selon un mapping validé."""
        ...
