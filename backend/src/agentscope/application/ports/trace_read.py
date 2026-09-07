"""Port de lecture des traces normalisées.

**C'est le contrat entre le lot 5 (dashboard) et le lot 2 (modèle de données).** Le lot 5
le déclare ici en fonction de ce dont ses indicateurs ont besoin ; le lot 2 l'implémente
au-dessus de PostgreSQL. Chacun avance de son côté sans attendre l'autre.

Trois choix structurants, à connaître avant d'implémenter :

1. **Le port renvoie des enregistrements, pas des agrégats.** Le calcul des indicateurs
   reste dans le domaine, donc testable sans base — c'est une exigence de l'énoncé. Si le
   volume l'impose plus tard, l'agrégation pourra descendre derrière ce même port, au prix
   de cette testabilité : ce sera une décision à documenter, pas un glissement silencieux.

2. **Toutes les mesures sont optionnelles.** Une source qui ne publie pas un compteur
   renvoie `None`, jamais `0`. Cela suppose que le modèle relationnel ne mette aucun
   `DEFAULT 0` sur une colonne de mesure — sinon l'information est perdue avant d'arriver
   ici, et plus rien en aval ne peut la retrouver.

3. **Chaque enregistrement porte son `session_id` et sa `source`.** C'est ce qui rend
   possible le retour d'un point de graphique vers les sessions correspondantes, et la
   séparation des métriques non comparables entre sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class TraceFilter:
    """Périmètre d'interrogation, commun à tous les écrans du dashboard.

    Un filtre vide signifie « tout ». Les bornes de période sont inclusives, et exprimées
    en dates : le dashboard raisonne en jours, pas en instants.
    """

    sources: tuple[str, ...] = field(default_factory=tuple)
    agents: tuple[str, ...] = field(default_factory=tuple)
    models: tuple[str, ...] = field(default_factory=tuple)
    since: date | None = None
    until: date | None = None

    session_ids: tuple[str, ...] = field(default_factory=tuple)
    """Restreint le périmètre à des sessions nommées.

    C'est ce qui rend le retour d'un graphique vers les enregistrements uniforme : un clic
    sur une barre ou un point produit la liste des sessions concernées, qu'il suffit de
    repasser en filtre. Le détail d'une session n'est qu'un cas particulier à un élément.
    """

    def __post_init__(self) -> None:
        if self.since and self.until and self.since > self.until:
            raise ValueError(
                f"La borne de début ({self.since}) est postérieure à la borne de fin "
                f"({self.until})."
            )


@dataclass(frozen=True)
class SessionRecord:
    """Une ligne = une session, c'est-à-dire une suite d'échanges avec un agent."""

    session_id: str
    source: str
    agent: str
    started_at: datetime | None
    ended_at: datetime | None


@dataclass(frozen=True)
class ModelCallRecord:
    """Une ligne = une invocation du modèle."""

    session_id: str
    source: str
    agent: str
    model: str | None
    occurred_at: datetime | None
    input_tokens: int | None
    output_tokens: int | None
    cache_creation_tokens: int | None


@dataclass(frozen=True)
class ToolCallRecord:
    """Une ligne = un appel d'outil.

    `is_error` vaut `None` quand la source ne publie pas l'issue de l'appel. C'est une
    troisième valeur, distincte de « réussi » et de « échoué », et le taux d'erreur la
    traite comme telle.
    """

    session_id: str
    source: str
    tool_name: str
    occurred_at: datetime | None
    is_error: bool | None
    latency_ms: int | None


class TraceReadPort(ABC):
    """Lecture des traces normalisées, filtrées."""

    @abstractmethod
    def sessions(self, filters: TraceFilter) -> Sequence[SessionRecord]: ...

    @abstractmethod
    def model_calls(self, filters: TraceFilter) -> Sequence[ModelCallRecord]: ...

    @abstractmethod
    def tool_calls(self, filters: TraceFilter) -> Sequence[ToolCallRecord]: ...
