"""Contrat de lecture de l'historique des imports.

Ce port ne dépend pas du moteur d'import : il expose seulement les informations déjà
persistées pour permettre à l'interface de présenter l'historique des opérations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ImportRecord:
    """Résumé immuable d'une opération d'import terminée ou en échec."""

    import_id: str
    source: str
    filename: str
    format: str
    imported_at: datetime
    status: str
    records_imported: int
    duplicates_count: int
    rejected_count: int
    missing_data_count: int


@dataclass(frozen=True)
class RejectionRecord:
    """Un enregistrement refusé par un import, tel qu'il a été conservé."""

    line_number: int
    reason: str
    raw_preview: str | None


class ImportReadPort(ABC):
    """Lecture des opérations d'import persistées."""

    @abstractmethod
    def list_imports(self) -> Sequence[ImportRecord]: ...

    @abstractmethod
    def rejections(self, import_id: str) -> Sequence[RejectionRecord]:
        """Les enregistrements qu'un import a refusés, dans l'ordre du fichier.

        Une méthode à part de `list_imports` : l'historique se consulte souvent, le détail
        des rejets rarement, et rien ne justifie de charger le second à chaque fois qu'on
        demande le premier.
        """
        ...
