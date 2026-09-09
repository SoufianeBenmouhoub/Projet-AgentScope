"""Adaptateur SQLAlchemy pour détecter les imports déjà effectués."""

from __future__ import annotations

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from agentscope.application.ports.import_deduplication import (
    ImportDeduplicationPort,
)
from agentscope.infrastructure.persistence.models import Import


class SqlAlchemyImportDeduplication(ImportDeduplicationPort):
    """Détecte les imports existants à partir du hash du fichier."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def already_imported(self, file_hash: str) -> bool:
        """Retourne True si un import possède déjà ce hash de fichier."""
        with Session(self._engine) as session:
            statement = select(Import.id).where(Import.file_hash == file_hash)
            return session.scalar(statement) is not None
