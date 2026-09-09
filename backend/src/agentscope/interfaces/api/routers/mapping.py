"""Route de proposition de mapping par l'agent IA."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from agentscope.application.ports.mapping_proposal import build_import_sample
from agentscope.application.use_cases.propose_mapping import ProposeMapping
from agentscope.interfaces.api.dependencies import provide_propose_mapping
from agentscope.interfaces.api.schemas.mapping import (
    ImportSampleRequest,
    MappingProposalResponse,
)

router = APIRouter(prefix="/api/v1/mapping", tags=["mapping"])


@router.post(
    "/propose",
    response_model=MappingProposalResponse,
    summary="Propose une correspondance de champs pour un échantillon importé",
)
def propose_mapping(
    payload: ImportSampleRequest,
    use_case: Annotated[ProposeMapping, Depends(provide_propose_mapping)],
) -> MappingProposalResponse:
    """Construit un échantillon à partir des enregistrements bruts envoyés, puis demande
    à l'agent IA configuré (`AI_PROVIDER`) de proposer une correspondance vers le modèle
    du domaine. Une correspondance non trouvée reste `None`, jamais une supposition.
    """
    sample = build_import_sample(payload.records, source_format=payload.source_format)
    proposal = use_case(sample)
    return MappingProposalResponse.from_domain(proposal)
