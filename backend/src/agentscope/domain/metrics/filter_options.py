"""Les valeurs sur lesquelles il est possible de filtrer.

Un dashboard qui propose de filtrer par « modèle » sans dire lesquels sont disponibles
oblige l'utilisateur à deviner. Ces options sont donc dérivées des traces réellement
importées, jamais d'une liste écrite en dur.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FilterOptions:
    """Les choix offerts par les filtres, et les bornes de la période couverte.

    Les valeurs non renseignées sont absentes de ces listes : on ne propose pas de filtrer
    sur « modèle inconnu », car ce n'est pas une valeur, c'est une absence de valeur.

    `first_day` et `last_day` sont nuls quand aucun enregistrement n'est horodaté — auquel
    cas le filtre par période n'a rien à borner, et l'interface doit le dire plutôt que
    d'afficher un calendrier vide.
    """

    sources: tuple[str, ...]
    agents: tuple[str, ...]
    models: tuple[str, ...]
    first_day: date | None
    last_day: date | None

    def __post_init__(self) -> None:
        if self.first_day and self.last_day and self.first_day > self.last_day:
            raise ValueError(
                f"La première journée observée ({self.first_day}) ne peut pas être "
                f"postérieure à la dernière ({self.last_day})."
            )

    @property
    def is_empty(self) -> bool:
        """Aucune trace n'a été importée : il n'y a rien à filtrer."""
        return not (self.sources or self.agents or self.models)
