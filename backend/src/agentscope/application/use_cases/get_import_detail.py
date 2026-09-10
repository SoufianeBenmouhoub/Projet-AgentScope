"""Détail d'une opération d'import : son bilan, et ce qu'elle a refusé."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.ports.import_read import (
    ImportReadPort,
    ImportRecord,
    RejectionRecord,
)


class ImportNotFound(Exception):
    """Aucun import ne porte cet identifiant."""

    def __init__(self, import_id: str) -> None:
        super().__init__(f"Aucun import « {import_id} » dans l'historique.")
        self.import_id = import_id


@dataclass(frozen=True)
class ImportDetail:
    """Le bilan d'un import et la liste des enregistrements qu'il a écartés.

    Les deux vont ensemble : un bilan qui annonce des rejets sans dire lesquels laisse
    l'utilisateur sans moyen de corriger son fichier.
    """

    record: ImportRecord
    rejections: tuple[RejectionRecord, ...]


class GetImportDetail:
    """Retrouve un import par son identifiant, avec le détail de ses rejets.

    La recherche du bilan se fait sur l'historique déjà exposé par le port : inutile
    d'élargir le contrat pour lire un élément d'une liste qu'on sait déjà lire.
    """

    def __init__(self, imports: ImportReadPort) -> None:
        self._imports = imports

    def execute(self, import_id: str) -> ImportDetail:
        for record in self._imports.list_imports():
            if record.import_id == import_id:
                return ImportDetail(
                    record=record,
                    rejections=tuple(self._imports.rejections(import_id)),
                )

        raise ImportNotFound(import_id)
