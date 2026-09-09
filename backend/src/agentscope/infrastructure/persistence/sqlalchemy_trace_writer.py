"""Adaptateur SQLAlchemy pour l'écriture des traces normalisées."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as SQLAlchemySession

from agentscope.application.ports.trace_write import TraceWritePort
from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall
from agentscope.infrastructure.persistence.models import (
    Import as ImportModel,
    ModelCall as ModelCallModel,
    Session as SessionModel,
    Source,
    ToolCall as ToolCallModel,
)


class SQLAlchemyTraceWriter(TraceWritePort):
    """Écrit les entités de trace dans PostgreSQL via SQLAlchemy."""

    def __init__(self, db: SQLAlchemySession) -> None:
        self._db = db

    def save_session(self, session: Session) -> None:
        source_name = session.provenance.source

        source = self._db.scalar(
            select(Source).where(Source.name == source_name)
        )

        if source is None:
            source = Source(
                name=source_name,
                agent_name=session.agent_name,
                created_at=datetime.now(timezone.utc),
            )
            self._db.add(source)
            self._db.flush()

        self._db.add(
            SessionModel(
                id=session.id,
                source_id=source.id,
                external_id=session.external_id,
                started_at=session.started_at,
                ended_at=session.ended_at,
                agent_name=session.agent_name,
                status=session.status,
            )
        )

    def save_model_call(self, model_call: ModelCall) -> None:
        self._db.add(
            ModelCallModel(
                id=model_call.id,
                session_id=model_call.session_id,
                external_id=model_call.external_id,
                model_name=model_call.model_name,
                started_at=model_call.started_at,
                ended_at=model_call.ended_at,
                input_tokens=model_call.input_tokens,
                output_tokens=model_call.output_tokens,
                cached_tokens=model_call.cached_tokens,
                status=model_call.status,
            )
        )

    def save_tool_call(self, tool_call: ToolCall) -> None:
        self._db.add(
            ToolCallModel(
                id=tool_call.id,
                session_id=tool_call.session_id,
                external_id=tool_call.external_id,
                tool_name=tool_call.tool_name,
                started_at=tool_call.started_at,
                ended_at=tool_call.ended_at,
                status=tool_call.status,
                error=tool_call.error,
            )
        )

    def save_source(self, name: str) -> UUID:
        """Crée ou récupère une source."""

        source = self._db.scalar(
            select(Source).where(Source.name == name)
        )

        if source is None:
            source = Source(
                name=name,
                created_at=datetime.now(timezone.utc),
            )
            self._db.add(source)
            self._db.flush()

        return source.id

    def save_import(
        self,
        source_id: UUID,
        filename: str,
        file_hash: str,
        file_format: str,
        records_imported: int,
        missing_data_count: int,
    ) -> None:
        """Enregistre une opération d'import."""

        self._db.add(
            ImportModel(
                source_id=source_id,
                filename=filename,
                file_hash=file_hash,
                format=file_format,
                imported_at=datetime.now(timezone.utc),
                status="completed",
                records_imported=records_imported,
                duplicates_count=0,
                rejected_count=0,
                missing_data_count=missing_data_count,
            )
        )

    def commit(self) -> None:
        """Valide la transaction en cours."""

        self._db.commit()
