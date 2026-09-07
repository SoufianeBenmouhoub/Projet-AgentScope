"""Exemple de référence : un port."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DatabaseHealthPort(ABC):
    """Permet de savoir si le stockage répond.

    Aucun cas d'utilisation ne connaît SQLAlchemy : ils passent tous par ce contrat, dont
    l'implémentation réelle vit dans `infrastructure/persistence/` et la doublure de test
    dans `tests/fakes/`.
    """

    @abstractmethod
    def is_reachable(self) -> bool:
        """Retourne True si le stockage répond, False sinon.

        Ne lève jamais : une indisponibilité est un résultat, pas une erreur de programme.
        """
