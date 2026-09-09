"""Lecture de l'historique des imports depuis PostgreSQL."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as DbSession

from agentscope.application.ports.import_read import ImportReadPort, ImportRecord
from agentscope.infrastructure.persistence.models import Import, Source


class SqlAlchemyImportRead(ImportReadPort):
    """Traduit les tables ``imports`` et ``sources`` vers le contrat applicatif."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_imports(self) -> Sequence[ImportRecord]:
        statement = select(Import, Source.name).join(Source, Import.source_id == Source.id)
        with DbSession(self._engine) as session:
            rows = session.execute(statement).all()

        return tuple(
            ImportRecord(
                import_id=str(import_row.id),
                source=source_name,
                filename=import_row.filename,
                format=import_row.format,
                imported_at=import_row.imported_at,
                status=import_row.status,
                records_imported=import_row.records_imported,
                duplicates_count=import_row.duplicates_count,
                rejected_count=import_row.rejected_count,
                missing_data_count=import_row.missing_data_count,
            )
            for import_row, source_name in rows
        )
