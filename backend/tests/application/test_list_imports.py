"""Tests de l'historique des imports."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from agentscope.application.ports.import_read import ImportReadPort, ImportRecord
from agentscope.application.use_cases.list_imports import ListImports


class InMemoryImportRead(ImportReadPort):
    def __init__(self, records: Sequence[ImportRecord] = ()) -> None:
        self._records = records

    def list_imports(self) -> Sequence[ImportRecord]:
        return self._records


def _import(
    import_id: str,
    *,
    imported_at: datetime = datetime(2026, 9, 3, 10, tzinfo=UTC),
    status: str = "completed",
    records_imported: int = 10,
    duplicates_count: int = 0,
    rejected_count: int = 0,
    missing_data_count: int = 0,
) -> ImportRecord:
    return ImportRecord(
        import_id=import_id,
        source="tracelab",
        filename=f"{import_id}.jsonl",
        format="jsonl",
        imported_at=imported_at,
        status=status,
        records_imported=records_imported,
        duplicates_count=duplicates_count,
        rejected_count=rejected_count,
        missing_data_count=missing_data_count,
    )


def test_retourne_les_imports_du_plus_recent_au_plus_ancien() -> None:
    oldest = _import("oldest", imported_at=datetime(2026, 9, 1, tzinfo=UTC))
    newest = _import("newest", imported_at=datetime(2026, 9, 4, tzinfo=UTC))

    history = ListImports(InMemoryImportRead([oldest, newest])).execute()

    assert [record.import_id for record in history] == ["newest", "oldest"]


def test_conserve_le_rapport_complet_d_un_import_partiellement_rejete() -> None:
    imported = _import(
        "batch-42",
        status="completed_with_warnings",
        records_imported=12,
        duplicates_count=2,
        rejected_count=3,
        missing_data_count=1,
    )

    history = ListImports(InMemoryImportRead([imported])).execute()

    assert history[0].status == "completed_with_warnings"
    assert history[0].records_imported == 12
    assert history[0].duplicates_count == 2
    assert history[0].rejected_count == 3
    assert history[0].missing_data_count == 1


def test_un_historique_vide_reste_vide() -> None:
    assert ListImports(InMemoryImportRead()).execute() == ()
