"""Exemple de référence : une entité de domaine.

Ce module sert de modèle aux autres lots. Trois choses à en retenir :

1. aucune importation en dehors de la bibliothèque standard ;
2. la règle métier est exprimée **ici**, pas dans le routeur ni dans le SQL ;
3. l'objet est immuable et refuse d'exister dans un état invalide.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComponentState(Enum):
    """État observé d'un composant dont l'application dépend."""

    OK = "ok"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class SystemStatus:
    """Relevé de santé de l'application à un instant donné.

    Une instance = un relevé complet. Rien n'est persisté.
    """

    version: str
    database: ComponentState

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("La version de l'application ne peut pas être vide.")

    @property
    def is_operational(self) -> bool:
        """L'application peut-elle rendre son service ?

        Le parcours principal — importer, vérifier, normaliser, explorer — repose
        entièrement sur le stockage. Sans lui, l'application est démarrée mais inutilisable :
        on distingue donc « en ligne » de « opérationnelle ».
        """
        return self.database is ComponentState.OK
