"""Aperçu d'un fichier avant import.

L'énoncé demande que l'utilisateur puisse « consulter un aperçu » avant de valider. C'est
aussi ce qui alimente l'agent IA : il ne reçoit qu'un échantillon et la liste des champs,
jamais le fichier entier.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentscope.application.ports.file_read import FileReadPort

#: Nombre de lignes montrées. Assez pour juger de la structure, assez peu pour ne pas
#: déverser le fichier dans l'interface ni dans une requête à un modèle.
DEFAULT_SAMPLE_SIZE = 20


@dataclass(frozen=True)
class FilePreview:
    """Ce qu'on peut dire d'un fichier sans l'importer."""

    filename: str
    file_format: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]

    @property
    def row_count_sample(self) -> int:
        return len(self.rows)


class PreviewImportFile:
    """Lit un échantillon du fichier et en déduit la liste des champs."""

    def __init__(self, file_reader: FileReadPort) -> None:
        self._file_reader = file_reader

    def execute(
        self,
        path: Path,
        file_format: str | None = None,
        limit: int = DEFAULT_SAMPLE_SIZE,
    ) -> FilePreview:
        rows = tuple(self._file_reader.sample(path, file_format, limit))

        return FilePreview(
            filename=path.name,
            file_format=(file_format or path.suffix.lstrip(".")).lower(),
            columns=_columns_of(rows),
            rows=rows,
        )


def _columns_of(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    """Les champs rencontrés, dans leur ordre d'apparition.

    L'union plutôt que les clés de la première ligne : un enregistrement peut omettre un
    champ que les suivants renseignent, et le taire ferait croire qu'il n'existe pas.
    """
    seen: dict[str, None] = {}
    for row in rows:
        for column in row:
            seen.setdefault(column, None)
    return tuple(seen)
