"""Tests du détail d'un import."""

from __future__ import annotations

import pytest

from agentscope.application.use_cases.get_import_detail import GetImportDetail, ImportNotFound
from tests.fakes.import_read import InMemoryImportRead, a_rejection, an_import


def test_retrouve_un_import_avec_ce_quil_a_refuse() -> None:
    reader = InMemoryImportRead(
        [an_import("batch-42", rejected_count=2)],
        rejections={"batch-42": (a_rejection(line_number=7), a_rejection(line_number=19))},
    )

    detail = GetImportDetail(reader).execute("batch-42")

    assert detail.record.import_id == "batch-42"
    assert [rejection.line_number for rejection in detail.rejections] == [7, 19]


def test_un_import_sans_rejet_rend_une_liste_vide() -> None:
    """Vide veut dire « rien n'a été refusé », pas « on ne sait pas »."""
    reader = InMemoryImportRead([an_import("batch-1")])

    detail = GetImportDetail(reader).execute("batch-1")

    assert detail.record.rejected_count == 0
    assert detail.rejections == ()


def test_les_rejets_dun_autre_import_ne_sont_pas_repris() -> None:
    reader = InMemoryImportRead(
        [an_import("batch-1"), an_import("batch-2")],
        rejections={"batch-2": (a_rejection(),)},
    )

    assert GetImportDetail(reader).execute("batch-1").rejections == ()


def test_un_identifiant_inconnu_est_signale_avec_lidentifiant_demande() -> None:
    reader = InMemoryImportRead([an_import("batch-1")])

    with pytest.raises(ImportNotFound) as error:
        GetImportDetail(reader).execute("batch-inconnu")

    assert "batch-inconnu" in str(error.value)
