"""Fourniture des cas d'utilisation et des filtres aux routeurs.

Le conteneur est déposé sur `app.state` au démarrage. Les routeurs n'appellent jamais
`build_container` eux-mêmes : ils reçoivent un cas d'utilisation déjà câblé, ce qui rend
chaque routeur testable en injectant des doublures.

`Depends` de FastAPI n'apparaît que dans cette couche.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import HTTPException, Query, Request

from agentscope.application.container import Container
from agentscope.application.ports.trace_read import TraceFilter
from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from agentscope.application.use_cases.get_filter_options import GetFilterOptions
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.application.use_cases.get_session_detail import GetSessionDetail
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from agentscope.application.use_cases.list_sessions import ListSessions
from agentscope.application.use_cases.propose_mapping import ProposeMapping


def provide_container(request: Request) -> Container:
    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - erreur de câblage, pas un cas nominal
        raise RuntimeError(
            "Aucun conteneur n'est attaché à l'application. "
            "L'application doit être construite via create_app(container=...)."
        )
    return container


def provide_get_system_status(request: Request) -> GetSystemStatus:
    return provide_container(request).get_system_status


def provide_get_kpi_summary(request: Request) -> GetKpiSummary:
    return provide_container(request).get_kpi_summary


def provide_get_tool_breakdown(request: Request) -> GetToolBreakdown:
    return provide_container(request).get_tool_breakdown


def provide_get_activity_series(request: Request) -> GetActivitySeries:
    return provide_container(request).get_activity_series


def provide_get_session_detail(request: Request) -> GetSessionDetail:
    return provide_container(request).get_session_detail


def provide_get_filter_options(request: Request) -> GetFilterOptions:
    return provide_container(request).get_filter_options


def provide_list_sessions(request: Request) -> ListSessions:
    return provide_container(request).list_sessions


def provide_propose_mapping(request: Request) -> ProposeMapping:
    return provide_container(request).propose_mapping


def provide_trace_filter(
    source: Annotated[list[str] | None, Query(description="Sources retenues.")] = None,
    agent: Annotated[list[str] | None, Query(description="Agents retenus.")] = None,
    model: Annotated[list[str] | None, Query(description="Modèles retenus.")] = None,
    session_id: Annotated[list[str] | None, Query(description="Sessions retenues.")] = None,
    since: Annotated[date | None, Query(description="Début de période, inclus.")] = None,
    until: Annotated[date | None, Query(description="Fin de période, incluse.")] = None,
) -> TraceFilter:
    """Traduit les paramètres de requête en périmètre, commun à toutes les routes.

    Un paramètre répété cumule les valeurs : `?source=a&source=b` retient les deux. Aucun
    paramètre signifie « tout », ce qui est le comportement attendu à l'ouverture du
    dashboard.
    """
    try:
        return TraceFilter(
            sources=tuple(source or ()),
            agents=tuple(agent or ()),
            models=tuple(model or ()),
            session_ids=tuple(session_id or ()),
            since=since,
            until=until,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
