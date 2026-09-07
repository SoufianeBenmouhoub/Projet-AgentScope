"""Série d'activité dans le temps.

Alimente la visualisation « quand les agents ont-ils travaillé », et rend visible ce qui
ne peut pas y figurer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ActivityPoint:
    """Une journée d'activité.

    Les trois compteurs sont des dénombrements : zéro y est une vraie valeur, pas une
    absence. Une journée sans activité au milieu de la période vaut donc réellement zéro.
    """

    day: date
    sessions: int
    model_calls: int
    tool_calls: int
    session_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActivitySeries:
    """Série continue, avec le décompte de ce qui n'a pas pu y être placé.

    Un enregistrement sans horodatage n'appartient à aucune journée. Le supprimer
    silencieusement de la série ferait mentir le graphique : les compteurs `undated_*`
    existent pour que l'interface puisse le dire. Ils alimentent aussi le panneau de
    qualité des données.
    """

    points: tuple[ActivityPoint, ...]
    undated_sessions: int
    undated_model_calls: int
    undated_tool_calls: int

    @property
    def has_undated_records(self) -> bool:
        return bool(self.undated_sessions or self.undated_model_calls or self.undated_tool_calls)
