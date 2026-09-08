"""Route de la vue détaillée d'une session."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from agentscope.application.ports.trace_read import TraceFilter
from agentscope.application.use_cases.get_session_detail import (
    GetSessionDetail,
    SessionNotFound,
)
from agentscope.application.use_cases.list_sessions import ListSessions
from agentscope.interfaces.api.dependencies import (
    provide_get_session_detail,
    provide_list_sessions,
    provide_trace_filter,
)
from agentscope.interfaces.api.schemas.sessions import SessionDetailResponse, SessionListResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse, summary="Sessions du périmètre")
def list_sessions(
    filters: Annotated[TraceFilter, Depends(provide_trace_filter)],
    use_case: Annotated[ListSessions, Depends(provide_list_sessions)],
) -> SessionListResponse:
    """Accepte les mêmes filtres que le dashboard, `session_id` compris.

    C'est ce qui permet de partir d'un point de graphique — qui porte ses identifiants de
    sessions — et d'arriver aux enregistrements correspondants.
    """
    return SessionListResponse.from_domain(use_case.execute(filters))


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
