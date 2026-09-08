"""Port de lecture générique des fichiers de traces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any


class FileReadPort(ABC):
    """Contrat de lecture des fichiers sources."""

    @abstractmethod
    def read(
        self,
        path: Path,
        file_format: str | None = None,
    ) -> Sequence[dict[str, Any]]:
        """Lit un fichier source et retourne ses enregistrements bruts."""
        ...

    @abstractmethod
    def sample(
        self,
        path: Path,
        file_format: str | None = None,
        limit: int = 100,
    ) -> Sequence[dict[str, Any]]:
        """Retourne un échantillon des enregistrements bruts."""
        ...
