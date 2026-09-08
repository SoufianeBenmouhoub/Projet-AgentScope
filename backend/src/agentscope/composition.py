"""Racine de composition.

**Le seul endroit du projet où les implémentations concrètes sont choisies.** Changer de
moteur de stockage ou de fournisseur d'IA se joue ici, en une ligne, sans toucher aux
règles métier.

C'est aussi le seul module, avec `main.py`, autorisé à importer `infrastructure/`.
"""

from __future__ import annotations

from agentscope.application.container import Container
from agentscope.application.ports.mapping_proposal import MappingProposalPort
from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.application.use_cases.get_session_detail import GetSessionDetail
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from agentscope.application.use_cases.propose_mapping import ProposeMapping
from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.infrastructure.llm.fake import FakeMappingProposal
from agentscope.infrastructure.llm.ollama import OllamaMappingProposal
from agentscope.infrastructure.persistence.empty_trace_read import EmptyTraceRead
from agentscope.infrastructure.persistence.engine import build_engine
from agentscope.infrastructure.persistence.sqlalchemy_database_health import (
    SqlAlchemyDatabaseHealth,
)


def build_mapping_proposal(settings: Settings) -> MappingProposalPort:
    """Choisit l'adaptateur IA à utiliser selon la configuration."""
    if settings.ai_provider == "fake":
        return FakeMappingProposal()
    if settings.ai_provider == "ollama":
        return OllamaMappingProposal(
            model=settings.ai_model,
            base_url=settings.ai_base_url or "http://localhost:11434/v1",
        )
    raise NotImplementedError(
        f"Fournisseur IA non pris en charge pour l'instant : {settings.ai_provider}"
    )


def build_container(settings: Settings | None = None) -> Container:
    """Câble les cas d'utilisation avec leurs implémentations réelles."""
    settings = settings or get_settings()
    engine = build_engine(settings.database_url)

    # Lecture des traces. Tant que le lot 2 n'a pas livré le stockage, l'application ne lit
    # rien et l'annonce. Le jour où `SqlAlchemyTraceRead` existe, c'est cette ligne — et
    # elle seule — qui change.
    traces = EmptyTraceRead()

    return Container(
        get_system_status=GetSystemStatus(
            database_health=SqlAlchemyDatabaseHealth(engine),
            version=settings.app_version,
        ),
        propose_mapping=ProposeMapping(
            mapping_proposal=build_mapping_proposal(settings),
        ),
        get_kpi_summary=GetKpiSummary(traces),
        get_tool_breakdown=GetToolBreakdown(traces),
        get_activity_series=GetActivitySeries(traces),
        get_session_detail=GetSessionDetail(traces),
    )