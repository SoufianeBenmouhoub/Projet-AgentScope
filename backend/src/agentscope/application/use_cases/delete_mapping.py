"""Cas d'utilisation : retirer un mapping de la bibliothèque."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.ports.mapping_store import MappingStorePort


class MappingNotFound(Exception):
    """Aucun mapping enregistré ne porte cet identifiant."""

    def __init__(self, mapping_id: str) -> None:
        super().__init__(f"Aucun mapping enregistré « {mapping_id} ».")
        self.mapping_id = mapping_id


@dataclass(frozen=True)
class DeleteMapping:
    """Supprime un mapping enregistré.

    Une suppression qui ne trouve rien est signalée plutôt que tue : croire avoir supprimé
    un mapping qui existe toujours mène à le retrouver plus tard sans comprendre pourquoi.
    """

    store: MappingStorePort

    def __call__(self, mapping_id: str) -> None:
        if not self.store.delete(mapping_id):
            raise MappingNotFound(mapping_id)
