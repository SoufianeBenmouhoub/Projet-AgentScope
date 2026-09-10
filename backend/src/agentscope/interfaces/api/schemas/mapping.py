"""Schémas HTTP du mapping : contrat, proposition, essai à blanc, bibliothèque."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from agentscope.application.ports.mapping_proposal import FieldMapping, MappingProposal
from agentscope.application.ports.mapping_store import SavedMapping
from agentscope.application.use_cases.preview_mapping import FieldOutcome, MappingPreview
from agentscope.domain.mapping.contract import TargetField


class ImportSampleRequest(BaseModel):
    """Échantillon brut envoyé par le client : un aperçu du fichier à importer."""

    source_format: str = Field(description="Format du fichier source : jsonl, csv, parquet.")
    records: list[dict[str, Any]] = Field(
        description="Quelques enregistrements bruts, tels que lus dans le fichier."
    )


class TargetFieldResponse(BaseModel):
    """Un champ du modèle commun qu'un mapping peut renseigner."""

    key: str
    scope: str = Field(description="session, model_call, tool_call ou collection.")
    description: str
    required: bool

    @classmethod
    def from_domain(cls, field: TargetField) -> TargetFieldResponse:
        return cls(
            key=field.key,
            scope=field.scope.value,
            description=field.description,
            required=field.required,
        )


class MappingContractResponse(BaseModel):
    """La liste fermée des champs visés, telle que le domaine la déclare.

    L'interface la lit au lieu de la recopier : une liste dupliquée finirait par proposer
    des champs que le moteur d'import refuse.
    """

    fields: list[TargetFieldResponse]


class FieldMappingResponse(BaseModel):
    target_field: str
    source_field: str | None
    confidence: float | None
    note: str | None

    @classmethod
    def from_domain(cls, mapping: FieldMapping) -> FieldMappingResponse:
        return cls(
            target_field=mapping.target_field,
            source_field=mapping.source_field,
            confidence=mapping.confidence,
            note=mapping.note,
        )


class MappingProposalResponse(BaseModel):
    mappings: list[FieldMappingResponse]
    unresolved_notes: list[str]

    @classmethod
    def from_domain(cls, proposal: MappingProposal) -> MappingProposalResponse:
        return cls(
            mappings=[FieldMappingResponse.from_domain(m) for m in proposal.mappings],
            unresolved_notes=list(proposal.unresolved_notes),
        )


class MappingPreviewRequest(BaseModel):
    """Un échantillon et un mapping à essayer dessus, sans rien écrire."""

    records: list[dict[str, Any]]
    mapping: dict[str, str | None]
    source_name: str = ""


class FieldOutcomeResponse(BaseModel):
    """Ce qu'un champ donnerait sur l'échantillon."""

    target_field: str
    path: str | None
    scope: str
    required: bool
    examples: list[str] = Field(description="Valeurs réellement lues, tronquées.")
    resolved: int = Field(description="Enregistrements où le chemin mène à une valeur.")
    total: int

    @classmethod
    def from_domain(cls, outcome: FieldOutcome) -> FieldOutcomeResponse:
        return cls(
            target_field=outcome.target_field,
            path=outcome.path,
            scope=outcome.scope,
            required=outcome.required,
            examples=list(outcome.examples),
            resolved=outcome.resolved,
            total=outcome.total,
        )


class MappingPreviewResponse(BaseModel):
    """Ce que l'import produirait avec ce mapping, sans l'avoir lancé."""

    fields: list[FieldOutcomeResponse]
    records: int
    sessions: int
    model_calls: int
    tool_calls: int
    issues: list[str]
    rejected: int

    @classmethod
    def from_domain(cls, preview: MappingPreview) -> MappingPreviewResponse:
        return cls(
            fields=[FieldOutcomeResponse.from_domain(field) for field in preview.fields],
            records=preview.records,
            sessions=preview.sessions,
            model_calls=preview.model_calls,
            tool_calls=preview.tool_calls,
            issues=list(preview.issues),
            rejected=preview.rejected,
        )


class SaveMappingRequest(BaseModel):
    """Un mapping vérifié, à conserver sous un nom."""

    name: str = Field(description="Nom sous lequel le retrouver. Réenregistrer remplace.")
    source_name: str | None = None
    mapping: dict[str, str | None]


class SavedMappingResponse(BaseModel):
    id: str
    name: str
    source_name: str | None
    mapping: dict[str, str | None]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, saved: SavedMapping) -> SavedMappingResponse:
        return cls(
            id=saved.mapping_id,
            name=saved.name,
            source_name=saved.source_name,
            mapping=saved.fields,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )


class SavedMappingListResponse(BaseModel):
    mappings: list[SavedMappingResponse]
