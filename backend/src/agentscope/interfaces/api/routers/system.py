"""Exemple de référence : un routeur.

Un routeur fait trois choses et rien d'autre : recevoir, déléguer à un cas d'utilisation,
traduire le résultat en schéma de sortie. Aucune règle métier, aucune requête SQL.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.interfaces.api.dependencies import provide_get_system_status
from agentscope.interfaces.api.schemas.system import SystemStatusResponse

router = APIRouter(prefix="/api/v1/system", tags=["système"])


@router.get("/status", response_model=SystemStatusResponse, summary="État de l'application")
def read_system_status(
    use_case: Annotated[GetSystemStatus, Depends(provide_get_system_status)],
) -> SystemStatusResponse:
    status = use_case.execute()
    return SystemStatusResponse(
        version=status.version,
        database=status.database.value,
        operational=status.is_operational,
    )
