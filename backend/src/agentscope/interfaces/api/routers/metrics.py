"""Routes des indicateurs et des visualisations du dashboard.

Un routeur reçoit, délègue à un cas d'utilisation, traduit le résultat. Aucune règle
métier, aucune requête : les définitions d'indicateurs et le traitement des valeurs
absentes vivent dans le domaine, et cette couche ne fait que les transmettre fidèlement.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from agentscope.application.ports.trace_read import TraceFilter
from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from agentscope.domain.metrics.catalog import INDICATORS
from agentscope.interfaces.api.dependencies import (
    provide_get_activity_series,
    provide_get_kpi_summary,
    provide_get_tool_breakdown,
    provide_trace_filter,
)
from agentscope.interfaces.api.schemas.metrics import (
    ActivitySeriesResponse,
    IndicatorCatalogResponse,
    IndicatorDefinitionResponse,
    IndicatorResponse,
    KpiSummaryResponse,
    ToolBreakdownResponse,
)

router = APIRouter(prefix="/api/v1/metrics", tags=["indicateurs"])

Filters = Annotated[TraceFilter, Depends(provide_trace_filter)]


@router.get(
    "/definitions",
    response_model=IndicatorCatalogResponse,
    summary="Définitions des indicateurs",
)
def read_indicator_definitions() -> IndicatorCatalogResponse:
    """Le catalogue complet, consultable même quand aucune donnée n'a encore été importée."""
    return IndicatorCatalogResponse(
        definitions=[IndicatorDefinitionResponse.from_domain(item) for item in INDICATORS]
    )


@router.get("/summary", response_model=KpiSummaryResponse, summary="Synthèse des indicateurs")
def read_kpi_summary(
    filters: Filters,
    use_case: Annotated[GetKpiSummary, Depends(provide_get_kpi_summary)],
) -> KpiSummaryResponse:
    return KpiSummaryResponse(
        indicators=[IndicatorResponse.from_domain(item) for item in use_case.execute(filters)]
    )


@router.get("/tools", response_model=ToolBreakdownResponse, summary="Répartition des outils")
def read_tool_breakdown(
    filters: Filters,
    use_case: Annotated[GetToolBreakdown, Depends(provide_get_tool_breakdown)],
) -> ToolBreakdownResponse:
    return ToolBreakdownResponse.from_domain(use_case.execute(filters))


@router.get("/activity", response_model=ActivitySeriesResponse, summary="Activité dans le temps")
def read_activity_series(
    filters: Filters,
    use_case: Annotated[GetActivitySeries, Depends(provide_get_activity_series)],
) -> ActivitySeriesResponse:
    return ActivitySeriesResponse.from_domain(use_case.execute(filters))
