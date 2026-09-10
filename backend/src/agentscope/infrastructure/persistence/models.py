"""Tables SQLAlchemy du modèle de données AgentScope."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base déclarative commune à toutes les tables du modèle."""


class Source(Base):
    """Origine d'un jeu de traces ou d'un dataset."""

    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class Import(Base):
    """Opération d'importation d'un fichier."""

    __tablename__ = "imports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    records_imported: Mapped[int] = mapped_column(Integer, nullable=False)
    duplicates_count: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_data_count: Mapped[int] = mapped_column(Integer, nullable=False)


class Mapping(Base):
    """Un mapping mis au point par l'utilisateur, conservé pour être rejoué.

    `fields` est un document JSON plutôt qu'une table de correspondances : les champs du
    modèle commun sont déclarés dans le domaine, et les figer en colonnes obligerait à une
    migration à chaque champ ajouté.
    """

    __tablename__ = "mappings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fields: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImportRejection(Base):
    """Un enregistrement qu'un import n'a pas pu retenir, et la raison du refus.

    Une table à part plutôt qu'un compteur sur `imports` : un nombre dit qu'il y a eu un
    problème, il ne permet pas de le corriger. Ici, chaque rejet garde son rang dans le
    fichier et le début de la ligne d'origine, de quoi aller la voir.
    """

    __tablename__ = "import_rejections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_id: Mapped[UUID] = mapped_column(
        ForeignKey("imports.id"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    raw_preview: Mapped[str | None] = mapped_column(Text, nullable=True)


class RawRecord(Base):
    """Enregistrement original provenant d'un fichier importé."""

    __tablename__ = "raw_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_id: Mapped[UUID] = mapped_column(
        ForeignKey("imports.id"),
        nullable=False,
    )
    record_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    record_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "import_id",
            "record_hash",
            name="uq_raw_records_import_hash",
        ),
    )


class Session(Base):
    """Session complète d'utilisation d'un agent."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
    )
    raw_record_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("raw_records.id"),
        nullable=True,
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    agent_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


class ModelCall(Base):
    """Appel individuel à un modèle IA pendant une session."""

    __tablename__ = "model_calls"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("sessions.id"),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    cached_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


class ToolCall(Base):
    """Appel individuel à un outil pendant une session."""

    __tablename__ = "tool_calls"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("sessions.id"),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    tool_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    # Trois états : vrai, faux, et NULL quand la source ne publie pas l'issue. Le taux
    # d'erreur exclut ce dernier cas de son dénominateur plutôt que de le compter comme une
    # réussite. Sans valeur par défaut, pour la même raison que les colonnes de mesure.
    is_error: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
