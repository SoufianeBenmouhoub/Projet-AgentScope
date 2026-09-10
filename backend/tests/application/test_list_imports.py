"""Tests de l'historique des imports."""

from __future__ import annotations

from datetime import UTC, datetime

from agentscope.application.use_cases.list_imports import ListImports
from tests.fakes.import_read import InMemoryImportRead, an_import


def test_retourne_les_imports_du_plus_recent_au_plus_ancien() -> None:
    oldest = an_import("oldest", imported_at=datetime(2026, 9, 1, tzinfo=UTC))
    newest = an_import("newest", imported_at=datetime(2026, 9, 4, tzinfo=UTC))

    history = ListImports(InMemoryImportRead([oldest, newest])).execute()

    assert [record.import_id for record in history] == ["newest", "oldest"]


def test_conserve_le_rapport_complet_d_un_import_partiellement_rejete() -> None:
    imported = an_import(
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
