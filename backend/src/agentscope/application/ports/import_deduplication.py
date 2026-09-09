"""Port de détection des imports déjà effectués."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ImportDeduplicationPort(ABC):
    """Contrat permettant de détecter un fichier déjà importé."""

    @abstractmethod
    def already_imported(self, file_hash: str) -> bool:
        """Retourne True si un import avec ce hash existe déjà."""
        ...
