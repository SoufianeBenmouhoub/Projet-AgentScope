"""Racine de composition.

**Le seul endroit du projet où les implémentations concrètes sont choisies.** Changer de
moteur de stockage ou de fournisseur d'IA se joue ici, en une ligne, sans toucher aux
règles métier.

C'est aussi le seul module, avec `main.py`, autorisé à importer `infrastructure/`.
"""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from agentscope.application.container import Container
from agentscope.application.ports.mapping_proposal import MappingProposalPort
from agentscope.application.use_cases.get_activity_series import GetActivitySeries
from agentscope.application.use_cases.get_filter_options import GetFilterOptions
from agentscope.application.use_cases.get_import_detail import GetImportDetail
from agentscope.application.use_cases.get_kpi_summary import GetKpiSummary
from agentscope.application.use_cases.get_session_detail import GetSessionDetail
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from agentscope.application.use_cases.import_traces import ImportTraces
from agentscope.application.use_cases.list_imports import ListImports
from agentscope.application.use_cases.list_sessions import ListSessions
from agentscope.application.use_cases.preview_import_file import PreviewImportFile
from agentscope.application.use_cases.propose_mapping import ProposeMapping
from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.infrastructure.llm.fake import FakeMappingProposal
from agentscope.infrastructure.llm.ollama import OllamaMappingProposal
from agentscope.infrastructure.normalization.record_normalizer import RecordNormalizer
from agentscope.infrastructure.persistence.engine import build_engine
from agentscope.infrastructure.persistence.sqlalchemy_database_health import (
    SqlAlchemyDatabaseHealth,
)
from agentscope.infrastructure.persistence.sqlalchemy_import_deduplication import (
    SqlAlchemyImportDeduplication,
)
from agentscope.infrastructure.persistence.sqlalchemy_import_read import SqlAlchemyImportRead
from agentscope.infrastructure.persistence.sqlalchemy_trace_read import SqlAlchemyTraceRead
from agentscope.infrastructure.persistence.sqlalchemy_trace_writer import SQLAlchemyTraceWriter
from agentscope.infrastructure.sources.duckdb_file_reader import DuckDBFileReader


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

    # Lecture des traces. Volontairement pas de repli sur une lecture vide en cas de base
    # injoignable : afficher « aucune donnée importée » alors que le stockage ne répond pas
    # serait un mensonge, et c'est précisément ce que ce projet s'interdit.
    traces = SqlAlchemyTraceRead(engine)

    # Écriture des traces. On passe une fabrique de sessions, pas une session : chaque
    # import ouvre la sienne et la referme en validant. Une session unique partagée par
    # toute la durée de vie de l'application ne serait jamais fermée, ne supporterait pas
    # deux requêtes simultanées, et resterait souillée après le premier échec.
    session_factory = sessionmaker(bind=engine)

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
        get_filter_options=GetFilterOptions(traces),
        list_sessions=ListSessions(traces),
        import_traces=ImportTraces(
            file_reader=DuckDBFileReader(),
            normalizer=RecordNormalizer(),
            trace_writer=SQLAlchemyTraceWriter(session_factory),
            deduplication=SqlAlchemyImportDeduplication(engine),
        ),
        preview_import_file=PreviewImportFile(DuckDBFileReader()),
        list_imports=ListImports(SqlAlchemyImportRead(engine)),
        get_import_detail=GetImportDetail(SqlAlchemyImportRead(engine)),
    )
