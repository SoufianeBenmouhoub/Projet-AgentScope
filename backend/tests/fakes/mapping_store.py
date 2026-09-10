"""Doublure en mémoire du port de conservation des mappings."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from agentscope.application.ports.mapping_store import MappingStorePort, SavedMapping


class InMemoryMappingStore(MappingStorePort):
    """Conserve les mappings dans un dictionnaire, avec une horloge qui avance.

    L'horloge avance d'une seconde à chaque enregistrement : sans cela, deux mappings
    enregistrés dans le même test porteraient la même date, et l'ordre « du plus récemment
    modifié au plus ancien » ne serait pas vérifiable.
    """

    def __init__(self, mappings: Sequence[SavedMapping] = ()) -> None:
        self._by_id = {saved.mapping_id: saved for saved in mappings}
        self._now = datetime(2026, 9, 11, 9, tzinfo=UTC)

    def _tick(self) -> datetime:
        self._now += timedelta(seconds=1)
        return self._now

    def save(
        self, name: str, source_name: str | None, fields: dict[str, str | None]
    ) -> SavedMapping:
        moment = self._tick()
        existing = next((saved for saved in self._by_id.values() if saved.name == name), None)

        saved = SavedMapping(
            mapping_id=existing.mapping_id if existing else str(uuid4()),
            name=name,
            source_name=source_name,
            fields=dict(fields),
            created_at=existing.created_at if existing else moment,
            updated_at=moment,
        )
        self._by_id[saved.mapping_id] = saved
        return saved

    def list_mappings(self) -> Sequence[SavedMapping]:
        return tuple(self._by_id.values())

    def get(self, mapping_id: str) -> SavedMapping | None:
        return self._by_id.get(mapping_id)

    def delete(self, mapping_id: str) -> bool:
        return self._by_id.pop(mapping_id, None) is not None
