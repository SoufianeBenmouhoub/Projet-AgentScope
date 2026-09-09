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


class ImportReadPort(ABC):
    """Lecture des opérations d'import persistées."""

    @abstractmethod
    def list_imports(self) -> Sequence[ImportRecord]: ...
