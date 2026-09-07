"""Répartition des appels d'outils.

Alimente la visualisation « quels outils sont réellement utilisés », et le retour de cette
visualisation vers les sessions concernées.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.domain.metrics.aggregation import Aggregate


@dataclass(frozen=True)
class ToolUsage:
    """Usage observé d'un outil sur le périmètre filtré.

    `session_ids` n'est pas décoratif : c'est ce qui permet à l'utilisateur de cliquer sur
    une barre du graphique et de retrouver les sessions correspondantes, comme l'énoncé
    l'exige.
    """

    tool_name: str
    calls: Aggregate
    share: Aggregate
    error_rate: Aggregate
    median_latency: Aggregate
    session_ids: tuple[str, ...]


@dataclass(frozen=True)
class ToolBreakdown:
    """Répartition complète, ordonnée du plus utilisé au moins utilisé."""

    usages: tuple[ToolUsage, ...]
    tool_calls_total: int

    @property
    def distinct_tools(self) -> int:
        return len(self.usages)
