"""Schémas de l'import : aperçu, historique et bilan d'une opération."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from agentscope.application.ports.import_read import ImportRecord, RejectionRecord
from agentscope.application.use_cases.get_import_detail import ImportDetail
from agentscope.application.use_cases.preview_import_file import FilePreview


class ImportPreviewResponse(BaseModel):
    """Ce qu'on peut dire d'un fichier avant de l'importer."""

    filename: str
    format: str
    row_count_sample: int = Field(description="Nombre de lignes de l'échantillon lu.")
    columns: list[str] = Field(
        description="Champs rencontrés dans l'échantillon, dans leur ordre d'apparition."
    )
    sample_rows: list[dict[str, Any]]

    @classmethod
    def from_domain(cls, preview: FilePreview) -> ImportPreviewResponse:
        return cls(
            filename=preview.filename,
            format=preview.file_format,
            row_count_sample=preview.row_count_sample,
            columns=list(preview.columns),
            sample_rows=[_serialisable(row) for row in preview.rows],
        )


class ImportRecordResponse(BaseModel):
    """Le bilan d'une opération d'import."""

    id: str
    source_name: str
    filename: str
    format: str
    imported_at: datetime
    status: str = Field(
        description="« completed » quand l'import a abouti, « duplicate » quand le fichier "
        "avait déjà été importé."
    )
    records_imported: int
    duplicates_count: int
    rejected_count: int
    missing_data_count: int = Field(
        description="Nombre d'informations manquantes relevées pendant la normalisation."
    )

    @classmethod
    def from_domain(cls, record: ImportRecord) -> ImportRecordResponse:
        return cls(
            id=record.import_id,
            source_name=record.source,
            filename=record.filename,
            format=record.format,
            imported_at=record.imported_at,
            status=record.status,
            records_imported=record.records_imported,
            duplicates_count=record.duplicates_count,
            rejected_count=record.rejected_count,
            missing_data_count=record.missing_data_count,
        )


class ImportListResponse(BaseModel):
    imports: list[ImportRecordResponse]


class ImportRejectionResponse(BaseModel):
    """Un enregistrement refusé, et la raison du refus."""

    line_number: int = Field(description="Rang de l'enregistrement dans le fichier, depuis 1.")
    reason: str
    raw_preview: str | None = Field(
        description="Début de l'enregistrement d'origine, pour le reconnaître."
    )

    @classmethod
    def from_domain(cls, rejection: RejectionRecord) -> ImportRejectionResponse:
        return cls(
            line_number=rejection.line_number,
            reason=rejection.reason,
            raw_preview=rejection.raw_preview,
        )


class ImportDetailResponse(ImportRecordResponse):
    """Le bilan d'un import, avec le détail de ses rejets.

    Une liste vide veut dire que l'import n'a rien refusé — pas qu'on ne sait pas ce qu'il
    a refusé.
    """

    rejections: list[ImportRejectionResponse] = []

    @classmethod
    def from_domain(cls, detail: ImportDetail) -> ImportDetailResponse:
        summary = ImportRecordResponse.from_domain(detail.record)
        return cls(
            **summary.model_dump(),
            rejections=[
                ImportRejectionResponse.from_domain(rejection) for rejection in detail.rejections
            ],
        )


def _serialisable(row: dict[str, Any]) -> dict[str, Any]:
    """Rend une ligne brute transmissible en JSON.

    Un lecteur de fichiers peut rendre des dates ou des types que JSON ne connaît pas ; on
    les présente sous leur forme textuelle plutôt que d'échouer sur l'aperçu.
    """
    return {key: value if _is_json_native(value) else str(value) for key, value in row.items()}


def _is_json_native(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool | list | dict)
