"""Routes du mapping : le contrat, la proposition, l'essai à blanc, la bibliothèque.

Ensemble, elles rendent le parcours réalisable **depuis l'interface** : l'agent IA propose,
l'utilisateur corrige, l'essai à blanc montre ce que ça donnerait, et le mapping vérifié
s'enregistre pour être rejoué. C'est ce que l'énoncé demande, et rien ici n'exige d'écrire
une ligne de code.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from agentscope.application.ports.mapping_proposal import (
    MappingProposalUnavailable,
    build_import_sample,
)
from agentscope.application.use_cases.delete_mapping import DeleteMapping, MappingNotFound
from agentscope.application.use_cases.list_mappings import ListMappings
from agentscope.application.use_cases.preview_mapping import PreviewMapping
from agentscope.application.use_cases.propose_mapping import ProposeMapping
from agentscope.application.use_cases.save_mapping import SaveMapping
from agentscope.domain.mapping.contract import TARGET_FIELDS, InvalidMapping
from agentscope.domain.mapping.field_path import InvalidFieldPath
from agentscope.interfaces.api.dependencies import (
    provide_delete_mapping,
    provide_list_mappings,
    provide_preview_mapping,
    provide_propose_mapping,
    provide_save_mapping,
)
from agentscope.interfaces.api.schemas.mapping import (
    ImportSampleRequest,
    MappingContractResponse,
    MappingPreviewRequest,
    MappingPreviewResponse,
    MappingProposalResponse,
    SavedMappingListResponse,
    SavedMappingResponse,
    SaveMappingRequest,
    TargetFieldResponse,
)

router = APIRouter(prefix="/api/v1/mapping", tags=["mapping"])
library = APIRouter(prefix="/api/v1/mappings", tags=["mapping"])


@router.get(
    "/fields",
    response_model=MappingContractResponse,
    summary="Champs du modèle commun qu'un mapping peut renseigner",
)
def mapping_fields() -> MappingContractResponse:
    """La liste fermée que l'agent IA vise et que le moteur d'import applique.

    L'interface la lit ici plutôt que de la recopier : une liste dupliquée finirait par
    proposer des champs que le moteur refuse.
    """
    return MappingContractResponse(
        fields=[TargetFieldResponse.from_domain(field) for field in TARGET_FIELDS]
    )


@router.post(
    "/propose",
    response_model=MappingProposalResponse,
    summary="Propose une correspondance de champs pour un échantillon importé",
    responses={502: {"description": "Le fournisseur d'IA configuré n'a pas répondu."}},
)
def propose_mapping(
    payload: ImportSampleRequest,
    use_case: Annotated[ProposeMapping, Depends(provide_propose_mapping)],
) -> MappingProposalResponse:
    """Construit un échantillon à partir des enregistrements bruts envoyés, puis demande
    à l'agent IA configuré (`AI_PROVIDER`) de proposer une correspondance vers le modèle
    du domaine. Une correspondance non trouvée reste `None`, jamais une supposition.

    Un fournisseur injoignable donne 502, pas une proposition vide : « le service n'a pas
    répondu » et « aucun champ ne correspond » ne doivent pas se ressembler.
    """
    sample = build_import_sample(payload.records, source_format=payload.source_format)
    try:
        proposal = use_case(sample)
    except MappingProposalUnavailable as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return MappingProposalResponse.from_domain(proposal)


@router.post(
    "/preview",
    response_model=MappingPreviewResponse,
    summary="Essaie un mapping sur un échantillon, sans rien écrire",
    responses={422: {"description": "Mapping inapplicable."}},
)
def preview_mapping(
    payload: MappingPreviewRequest,
    use_case: Annotated[PreviewMapping, Depends(provide_preview_mapping)],
) -> MappingPreviewResponse:
    """Montre, champ par champ, les valeurs que le mapping lirait, et ce que l'import
    produirait — sessions, appels, anomalies, refus.

    C'est l'étape qui manque entre « l'IA propose » et « on importe » : sans elle, la seule
    façon de vérifier un mapping est de lancer l'import et de nettoyer la base ensuite.
    """
    try:
        return MappingPreviewResponse.from_domain(use_case(payload.records, payload.mapping))
    except (InvalidMapping, InvalidFieldPath) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@library.get("", response_model=SavedMappingListResponse, summary="Mappings enregistrés")
def list_mappings(
    use_case: Annotated[ListMappings, Depends(provide_list_mappings)],
) -> SavedMappingListResponse:
    """Les mappings conservés, du plus récemment modifié au plus ancien."""
    return SavedMappingListResponse(
        mappings=[SavedMappingResponse.from_domain(saved) for saved in use_case()]
    )


@library.post(
    "",
    response_model=SavedMappingResponse,
    summary="Enregistre un mapping vérifié",
    responses={422: {"description": "Mapping inapplicable, ou sans nom."}},
)
def save_mapping(
    payload: SaveMappingRequest,
    use_case: Annotated[SaveMapping, Depends(provide_save_mapping)],
) -> SavedMappingResponse:
    """Conserve le mapping sous ce nom, en remplaçant celui qui le portait déjà.

    Le mapping est validé avant d'être conservé : un mapping inapplicable enregistré
    aujourd'hui deviendrait une panne inexplicable le jour où quelqu'un le rechargerait.
    """
    try:
        saved = use_case(payload.name, payload.mapping, payload.source_name)
    except (InvalidMapping, InvalidFieldPath) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return SavedMappingResponse.from_domain(saved)


@library.delete(
    "/{mapping_id}",
    status_code=204,
    summary="Retire un mapping de la bibliothèque",
    responses={404: {"description": "Aucun mapping enregistré ne porte cet identifiant."}},
)
def delete_mapping(
    mapping_id: str,
    use_case: Annotated[DeleteMapping, Depends(provide_delete_mapping)],
) -> None:
    try:
        use_case(mapping_id)
    except MappingNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
