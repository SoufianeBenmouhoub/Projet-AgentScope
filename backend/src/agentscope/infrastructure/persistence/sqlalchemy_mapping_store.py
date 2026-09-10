"""Conservation des mappings dans PostgreSQL."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as DbSession

from agentscope.application.ports.mapping_store import MappingStorePort, SavedMapping
from agentscope.infrastructure.persistence.models import Mapping


class SqlAlchemyMappingStore(MappingStorePort):
    """Traduit la table ``mappings`` vers le contrat applicatif."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(
        self, name: str, source_name: str | None, fields: dict[str, str | None]
    ) -> SavedMapping:
        now = datetime.now(UTC)

        with DbSession(self._engine) as session:
            existing = session.scalar(select(Mapping).where(Mapping.name == name))

            if existing is None:
                existing = Mapping(
                    id=uuid4(),
                    name=name,
                    source_name=source_name,
                    fields=dict(fields),
                    created_at=now,
                    updated_at=now,
                )
                session.add(existing)
            else:
                existing.source_name = source_name
                existing.fields = dict(fields)
                existing.updated_at = now

            session.commit()
            return _to_domain(existing)

    def list_mappings(self) -> Sequence[SavedMapping]:
        with DbSession(self._engine) as session:
            rows = session.scalars(select(Mapping)).all()
            return tuple(_to_domain(row) for row in rows)

    def get(self, mapping_id: str) -> SavedMapping | None:
        identifier = _as_uuid(mapping_id)
        if identifier is None:
            return None

        with DbSession(self._engine) as session:
            row = session.get(Mapping, identifier)
            return None if row is None else _to_domain(row)

    def delete(self, mapping_id: str) -> bool:
        identifier = _as_uuid(mapping_id)
        if identifier is None:
            return False

        with DbSession(self._engine) as session:
            row = session.get(Mapping, identifier)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True


def _as_uuid(value: str) -> UUID | None:
    """Un identifiant mal formé désigne un mapping qui n'existe pas.

    Le laisser partir jusqu'à PostgreSQL produirait une erreur de type, pas une réponse.
    """
    try:
        return UUID(value)
    except ValueError:
        return None


def _to_domain(row: Mapping) -> SavedMapping:
    return SavedMapping(
        mapping_id=str(row.id),
        name=row.name,
        source_name=row.source_name,
        fields=dict(row.fields),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
