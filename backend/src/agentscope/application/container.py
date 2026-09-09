"""Le conteneur des cas d'utilisation exposés à l'extérieur.

Il ne référence que des types de la couche application : c'est `composition.py` qui décide
des implémentations concrètes qui les alimentent. C'est ce qui permet à `interfaces/` de
recevoir des cas d'utilisation câblés sans jamais importer `infrastructure/`.

Chaque lot ajoute ici le ou les cas d'utilisation qu'il expose.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from agentscope.application.use_cases.get_filter_options import GetFilterOptions
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.application.use_cases.get_session_detail import GetSessionDetail
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from agentscope.application.use_cases.import_traces import ImportTraces
from agentscope.application.use_cases.list_sessions import ListSessions
from agentscope.application.use_cases.propose_mapping import ProposeMapping


@dataclass(frozen=True)
class Container:
    """Cas d'utilisation disponibles dans l'application."""

    get_system_status: GetSystemStatus
    propose_mapping: ProposeMapping
    get_kpi_summary: GetKpiSummary
    get_tool_breakdown: GetToolBreakdown
    get_activity_series: GetActivitySeries
    get_session_detail: GetSessionDetail
    get_filter_options: GetFilterOptions
    list_sessions: ListSessions

    # Optionnel pour conserver la compatibilité avec les tests existants
    # et les anciens consommateurs du Container.
    import_traces: ImportTraces | None = None
