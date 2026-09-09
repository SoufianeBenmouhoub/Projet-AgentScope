"""Schémas HTTP pour la proposition de mapping (agent IA)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agentscope.application.ports.mapping_proposal import FieldMapping, MappingProposal


class ImportSampleRequest(BaseModel):
    """Échantillon brut envoyé par le client : un aperçu du fichier à importer."""

    source_format: str = Field(description="Format du fichier source : jsonl, csv, parquet.")
    records: list[dict[str, Any]] = Field(
        description="Quelques enregistrements bruts, tels que lus dans le fichier."
    )


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
