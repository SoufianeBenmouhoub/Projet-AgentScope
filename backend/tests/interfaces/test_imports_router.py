"""Tests des routes d'import.

Ce sont elles qui rendent le parcours réalisable depuis l'interface — l'exigence qui sera
vérifiée à la correction. Elles tournent ici avec des doublures : aucun fichier réel,
aucune base.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from agentscope.application.container import Container
from agentscope.application.ports.file_read import FileReadPort
from agentscope.application.ports.import_read import ImportReadPort, ImportRecord
from agentscope.application.use_cases.list_imports import ListImports
from agentscope.application.use_cases.preview_import_file import PreviewImportFile
from agentscope.interfaces.api.app import create_app
from tests.interfaces.client import build_container


class FakeFileReader(FileReadPort):
    """Lit n'importe quel chemin en renvoyant des lignes fixées d'avance."""

    def __init__(self, rows: list[dict[str, Any]] | None = None, fails: bool = False) -> None:
        self._rows = rows if rows is not None else [{"sid": "s1", "who": "claude-code"}]
        self._fails = fails

    def read(self, path: Path, file_format: str | None = None) -> list[dict[str, Any]]:
        return self._sample_or_fail()

    def sample(
        self, path: Path, file_format: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return self._sample_or_fail()[:limit]

    def _sample_or_fail(self) -> list[dict[str, Any]]:
        if self._fails:
            raise ValueError("Format de fichier non supporté : xlsx")
        return list(self._rows)


class FakeImportRead(ImportReadPort):
    def __init__(self, records: list[ImportRecord] | None = None) -> None:
        self._records = records or []

    def list_imports(self) -> list[ImportRecord]:
        return list(self._records)


class RecordingImportTraces:
    """Doublure du moteur d'import : retient ce qu'on lui a demandé."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, path: Path, mapping: dict[str, str | None], source: str, **_: Any) -> None:
        self.calls.append({"path": path, "mapping": mapping, "source": source})


def an_import_record(filename: str = "extrait.jsonl") -> ImportRecord:
    return ImportRecord(
        import_id="11111111-1111-1111-1111-111111111111",
        source="tracelab",
        filename=filename,
        format="jsonl",
        imported_at=datetime(2026, 9, 11, 9, 0, tzinfo=UTC),
        status="completed",
        records_imported=42,
        duplicates_count=0,
        rejected_count=1,
        missing_data_count=3,
    )


def build(
    *,
    reader: FileReadPort | None = None,
    importer: Any = None,
    records: list[ImportRecord] | None = None,
) -> tuple[TestClient, RecordingImportTraces]:
    engine = importer or RecordingImportTraces()
    base = build_container()
    container = Container(
        get_system_status=base.get_system_status,
        propose_mapping=base.propose_mapping,
        get_kpi_summary=base.get_kpi_summary,
        get_tool_breakdown=base.get_tool_breakdown,
        get_activity_series=base.get_activity_series,
        get_session_detail=base.get_session_detail,
        get_filter_options=base.get_filter_options,
        list_sessions=base.list_sessions,
        import_traces=engine,
        preview_import_file=PreviewImportFile(reader or FakeFileReader()),
        list_imports=ListImports(FakeImportRead(records)),
    )
    return TestClient(create_app(container=container)), engine


def a_file(name: str = "extrait.jsonl", content: str = '{"sid": "s1"}') -> dict[str, Any]:
    return {"file": (name, content.encode("utf-8"), "application/x-ndjson")}


class TestHistorique:
    def test_expose_les_imports_passes(self) -> None:
        client, _ = build(records=[an_import_record()])

        payload = client.get("/api/v1/imports").json()

        assert payload["imports"][0]["filename"] == "extrait.jsonl"
        assert payload["imports"][0]["records_imported"] == 42
        assert payload["imports"][0]["rejected_count"] == 1

    def test_un_historique_vide_repond_sans_erreur(self) -> None:
        client, _ = build()

        assert client.get("/api/v1/imports").json() == {"imports": []}


class TestApercu:
    def test_deduit_les_champs_du_fichier(self) -> None:
        reader = FakeFileReader([{"sid": "s1", "who": "claude-code"}])
        client, _ = build(reader=reader)

        payload = client.post("/api/v1/imports/preview", files=a_file()).json()

        assert payload["columns"] == ["sid", "who"]
        assert payload["row_count_sample"] == 1
        assert payload["filename"] == "extrait.jsonl"

    def test_signale_les_champs_absents_des_premieres_lignes(self) -> None:
        """Taire un champ que seules les lignes suivantes renseignent ferait croire qu'il
        n'existe pas."""
        reader = FakeFileReader([{"sid": "s1"}, {"sid": "s2", "tokens": 12}])
        client, _ = build(reader=reader)

        payload = client.post("/api/v1/imports/preview", files=a_file()).json()

        assert payload["columns"] == ["sid", "tokens"]

    def test_un_format_inconnu_est_refuse_avec_une_explication(self) -> None:
        client, _ = build(reader=FakeFileReader(fails=True))

        response = client.post("/api/v1/imports/preview", files=a_file("extrait.xlsx"))

        assert response.status_code == 422
        assert "xlsx" in response.json()["detail"]

    def test_lapercu_necrit_rien(self) -> None:
        client, importer = build()

        client.post("/api/v1/imports/preview", files=a_file())

        assert importer.calls == []


class TestImport:
    def test_importe_avec_le_mapping_fourni(self) -> None:
        client, importer = build(records=[an_import_record()])
        mapping = {"session_id": "sid", "agent": "who"}

        response = client.post(
            "/api/v1/imports",
            files=a_file(),
            data={"source_name": "tracelab", "mapping": json.dumps(mapping)},
        )

        assert response.status_code == 200
        assert importer.calls[0]["source"] == "tracelab"
        assert importer.calls[0]["mapping"]["session_id"] == "sid"
        # Les champs non renseignés par le mapping restent explicitement absents.
        assert importer.calls[0]["mapping"]["occurred_at"] is None

    def test_renvoie_le_bilan_de_limport(self) -> None:
        client, _ = build(records=[an_import_record()])

        payload = client.post(
            "/api/v1/imports", files=a_file(), data={"source_name": "tracelab"}
        ).json()

        assert payload["filename"] == "extrait.jsonl"
        assert payload["missing_data_count"] == 3

    def test_sans_mapping_une_correspondance_a_lidentique_est_tentee(self) -> None:
        client, importer = build(records=[an_import_record()])

        client.post("/api/v1/imports", files=a_file(), data={"source_name": "autre-source"})

        assert importer.calls[0]["mapping"]["session_id"] == "session_id"

    def test_sans_mapping_utilise_le_prereglage_tracelab(self) -> None:
        client, importer = build(records=[an_import_record()])

        client.post("/api/v1/imports", files=a_file(), data={"source_name": "TraceLab"})

        mapping = importer.calls[0]["mapping"]
        assert mapping["session_id"] == "session_id"
        assert mapping["agent"] == "provider"
        assert mapping["occurred_at"] == "timing_events[0].timestamp"
        assert mapping["tools"] == "tools"
        assert mapping["tool_ended_at"] == "result_at"

    def test_un_mapping_qui_nest_pas_du_json_est_refuse(self) -> None:
        client, _ = build()

        response = client.post(
            "/api/v1/imports",
            files=a_file(),
            data={"source_name": "tracelab", "mapping": "ceci n'est pas du json"},
        )

        assert response.status_code == 422
        assert "JSON" in response.json()["detail"]

    def test_un_mapping_vers_un_champ_inconnu_est_refuse_avec_les_champs_acceptes(self) -> None:
        client, _ = build()

        response = client.post(
            "/api/v1/imports",
            files=a_file(),
            data={"source_name": "tracelab", "mapping": json.dumps({"tokens_magiques": "x"})},
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "tokens_magiques" in detail
        assert "session_id" in detail

    def test_un_mapping_invalide_nimporte_rien(self) -> None:
        client, importer = build()

        client.post(
            "/api/v1/imports",
            files=a_file(),
            data={"source_name": "tracelab", "mapping": "{"},
        )

        assert importer.calls == []

    def test_un_format_inconnu_est_refuse_avec_une_explication(self) -> None:
        class FailingImport:
            def __call__(self, **_: Any) -> None:
                raise ValueError("Format de fichier non supporté : xlsx")

        client, _ = build(importer=FailingImport())

        response = client.post(
            "/api/v1/imports", files=a_file("extrait.xlsx"), data={"source_name": "tracelab"}
        )

        assert response.status_code == 422
        assert "xlsx" in response.json()["detail"]
