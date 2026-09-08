"""Liste des sessions d'un périmètre.

C'est le chaînon qui rend le retour d'un graphique vers les enregistrements possible :
l'utilisateur clique sur une barre ou un point, obtient les sessions concernées, puis en
ouvre une.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agentscope.domain.metrics.aggregation import Aggregate


@dataclass(frozen=True)
class SessionSummary:
    """Une session vue de loin : de quoi la reconnaître et décider de l'ouvrir."""

    session_id: str
    source: str
    agent: str
    started_at: datetime | None
    ended_at: datetime | None
    duration: Aggregate
    model_calls: int
    tool_calls: int
    input_tokens: Aggregate


@dataclass(frozen=True)
class SessionList:
    """Les sessions retenues, et combien il y en avait en tout.

    La liste est plafonnée : un jour chargé peut contenir des milliers de sessions, et une
    page qui tente de toutes les afficher devient inutilisable. `total` reste le compte
    réel, pour que l'interface puisse dire ce qu'elle ne montre pas plutôt que de laisser
    croire à un périmètre plus petit qu'il n'est.
    """

    sessions: tuple[SessionSummary, ...]
    total: int

    def __post_init__(self) -> None:
        if len(self.sessions) > self.total:
            raise ValueError(
                f"Une liste ne peut pas contenir plus de sessions ({len(self.sessions)}) "
                f"que le total annoncé ({self.total})."
            )

    @property
    def is_truncated(self) -> bool:
        return len(self.sessions) < self.total
