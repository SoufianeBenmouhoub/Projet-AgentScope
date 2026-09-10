"""Fabrique de client de test.

Construit l'application avec un conteneur rempli de doublures : les tests d'API tournent
sans base de données, sans serveur et sans appel réseau. C'est ce que permet le fait que
`create_app` reçoive son conteneur au lieu de le construire.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi.testclient import TestClient

from agentscope.application.container import Container
from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
)
from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from agentscope.application.use_cases.get_filter_options import GetFilterOptions
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.application.use_cases.get_session_detail import GetSessionDetail
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from agentscope.application.use_cases.list_sessions import ListSessions
from agentscope.application.use_cases.propose_mapping import ProposeMapping
from agentscope.infrastructure.llm.fake import FakeMappingProposal
from agentscope.interfaces.api.app import create_app
from tests.fakes.database_health import FakeDatabaseHealth
from tests.fakes.trace_read import InMemoryTraceRead


def build_container(
    *,
    sessions: Sequence[SessionRecord] = (),
    model_calls: Sequence[ModelCallRecord] = (),
    tool_calls: Sequence[ToolCallRecord] = (),
    database_reachable: bool = True,
    version: str = "0.1.0",
) -> Container:
    """Le conteneur du tableau de bord, rempli de doublures.

    Les cas d'utilisation de l'import ne sont pas câblés ici : les tests qui les exercent
    fournissent leurs propres doublures, et ceux qui ne les touchent pas n'ont pas à
    connaître un lecteur de fichiers.
    """
    traces = InMemoryTraceRead(
        sessions=sessions,
        model_calls=model_calls,
        tool_calls=tool_calls,
    )

    return Container(
        get_system_status=GetSystemStatus(
            database_health=FakeDatabaseHealth(reachable=database_reachable),
            version=version,
        ),
        propose_mapping=ProposeMapping(
            mapping_proposal=FakeMappingProposal(),
        ),
        get_kpi_summary=GetKpiSummary(traces),
        get_tool_breakdown=GetToolBreakdown(traces),
        get_activity_series=GetActivitySeries(traces),
        get_session_detail=GetSessionDetail(traces),
        get_filter_options=GetFilterOptions(traces),
        list_sessions=ListSessions(traces),
    )


def build_client(
    *,
    sessions: Sequence[SessionRecord] = (),
    model_calls: Sequence[ModelCallRecord] = (),
    tool_calls: Sequence[ToolCallRecord] = (),
    database_reachable: bool = True,
    version: str = "0.1.0",
) -> TestClient:
    container = build_container(
        sessions=sessions,
        model_calls=model_calls,
        tool_calls=tool_calls,
        database_reachable=database_reachable,
        version=version,
    )

    return TestClient(create_app(container=container, version=version))
