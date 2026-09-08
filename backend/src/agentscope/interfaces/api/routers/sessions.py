"""Route de la vue détaillée d'une session."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from agentscope.application.use_cases.get_session_detail import (
    GetSessionDetail,
    SessionNotFound,
)
from agentscope.interfaces.api.dependencies import provide_get_session_detail
from agentscope.interfaces.api.schemas.sessions import SessionDetailResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Détail d'une session",
    responses={404: {"description": "Aucune session ne porte cet identifiant."}},
)
def read_session_detail(
    session_id: str,
    use_case: Annotated[GetSessionDetail, Depends(provide_get_session_detail)],
) -> SessionDetailResponse:
    try:
        detail = use_case.execute(session_id)
    except SessionNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return SessionDetailResponse.from_domain(detail)
