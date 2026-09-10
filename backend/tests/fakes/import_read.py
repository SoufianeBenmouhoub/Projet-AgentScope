"""Doublure en mémoire du port de lecture des imports."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from agentscope.application.ports.import_read import (
    ImportReadPort,
    ImportRecord,
    RejectionRecord,
)


class InMemoryImportRead(ImportReadPort):
    """Un historique d'imports fixé d'avance, avec les rejets de chacun."""

    def __init__(
        self,
        records: Sequence[ImportRecord] = (),
        rejections: dict[str, Sequence[RejectionRecord]] | None = None,
    ) -> None:
        self._records = records
        self._rejections = rejections or {}

    def list_imports(self) -> Sequence[ImportRecord]:
        return self._records

    def rejections(self, import_id: str) -> Sequence[RejectionRecord]:
        return self._rejections.get(import_id, ())


def an_import(
    import_id: str = "batch-1",
    *,
    source: str = "tracelab",
    filename: str | None = None,
    imported_at: datetime = datetime(2026, 9, 3, 10, tzinfo=UTC),
    status: str = "completed",
    records_imported: int = 10,
    duplicates_count: int = 0,
    rejected_count: int = 0,
    missing_data_count: int = 0,
) -> ImportRecord:
    return ImportRecord(
        import_id=import_id,
        source=source,
        filename=filename or f"{import_id}.jsonl",
        format="jsonl",
        imported_at=imported_at,
        status=status,
        records_imported=records_imported,
        duplicates_count=duplicates_count,
        rejected_count=rejected_count,
        missing_data_count=missing_data_count,
    )


def a_rejection(
    line_number: int = 7,
    reason: str = "session_id : Sans identifiant de session, l'enregistrement ne peut "
    "être rattaché.",
    raw_preview: str | None = '{"who": "claude"}',
) -> RejectionRecord:
    return RejectionRecord(line_number=line_number, reason=reason, raw_preview=raw_preview)
