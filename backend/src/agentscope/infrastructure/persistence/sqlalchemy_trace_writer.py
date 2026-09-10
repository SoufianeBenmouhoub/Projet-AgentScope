"""Adaptateur SQLAlchemy pour l'écriture des traces normalisées."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker

from agentscope.application.ports.trace_write import TraceWritePort
from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall
from agentscope.infrastructure.persistence.models import (
    Import as ImportModel,
)
from agentscope.infrastructure.persistence.models import (
    ModelCall as ModelCallModel,
)
from agentscope.infrastructure.persistence.models import (
    Session as SessionModel,
)
from agentscope.infrastructure.persistence.models import (
    Source,
)
from agentscope.infrastructure.persistence.models import (
    ToolCall as ToolCallModel,
)


class SQLAlchemyTraceWriter(TraceWritePort):
    """Écrit les entités de trace dans PostgreSQL via SQLAlchemy.

    **Une session par import, pas une pour toute la vie de l'application.** L'adaptateur
    reçoit une fabrique et ouvre sa session au premier écrit ; `commit` la valide puis la
    referme. Sans ça, une session unique resterait ouverte indéfiniment, ne supporterait
    pas deux imports simultanés, et resterait inutilisable après le premier échec.

    Un import qui échoue en cours de route laisse sa session dans un état invalide : elle
    est alors annulée et remplacée au début de l'import suivant, plutôt que de propager la
    panne.
    """

    def __init__(self, session_factory: sessionmaker[SQLAlchemySession]) -> None:
        self._session_factory = session_factory
        self._session: SQLAlchemySession | None = None

    @property
    def _db(self) -> SQLAlchemySession:
        """La session de l'import en cours, ouverte à la demande."""
        if self._session is not None and not self._session.is_active:
            # Transaction avortée par une erreur précédente : on repart proprement.
            self._session.rollback()
            self._session.close()
            self._session = None

        if self._session is None:
            self._session = self._session_factory()

        return self._session

    def save_session(self, session: Session) -> None:
        source_name = session.provenance.source

        source = self._db.scalar(select(Source).where(Source.name == source_name))

        if source is None:
            source = Source(
                name=source_name,
                agent_name=session.agent_name,
                created_at=datetime.now(UTC),
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

        # Envoi immédiat en base. Les tables ne déclarent pas de `relationship` : SQLAlchemy
        # ne connaît donc pas l'ordre d'insertion imposé par les clés étrangères, et peut
        # écrire un appel avant la session qu'il référence. Le coût reste faible — une
        # session couvre en général des dizaines d'appels, qui eux restent groupés.
        self._db.flush()

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
                is_error=tool_call.is_error,
                error=tool_call.error,
            )
        )

    def save_source(self, name: str) -> UUID:
        """Crée ou récupère une source."""

        source = self._db.scalar(select(Source).where(Source.name == name))

        if source is None:
            source = Source(
                name=name,
                created_at=datetime.now(UTC),
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
                imported_at=datetime.now(UTC),
                status="completed",
                records_imported=records_imported,
                duplicates_count=0,
                rejected_count=0,
                missing_data_count=missing_data_count,
            )
        )

    def commit(self) -> None:
        """Valide la transaction de l'import, puis referme sa session.

        Un échec de validation annule tout : un import à moitié écrit serait pire qu'un
        import refusé, puisqu'il produirait des indicateurs faux sans que rien ne le signale.
        """
        if self._session is None:
            return

        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        finally:
            self._session.close()
            self._session = None
