"""Cas d'utilisation : la bibliothèque des mappings enregistrés."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.ports.mapping_store import MappingStorePort, SavedMapping


@dataclass(frozen=True)
class ListMappings:
    """Les mappings conservés, du plus récemment modifié au plus ancien.

    Cet ordre est celui de l'usage : celui qu'on vient de mettre au point est presque
    toujours celui qu'on veut rejouer.
    """

    store: MappingStorePort

    def __call__(self) -> tuple[SavedMapping, ...]:
        return tuple(
            sorted(self.store.list_mappings(), key=lambda saved: saved.updated_at, reverse=True)
        )
