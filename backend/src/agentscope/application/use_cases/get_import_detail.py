"""Détail d'une opération d'import."""

from __future__ import annotations

from agentscope.application.ports.import_read import ImportReadPort, ImportRecord


class ImportNotFound(Exception):
    """Aucun import ne porte cet identifiant."""

    def __init__(self, import_id: str) -> None:
        super().__init__(f"Aucun import « {import_id} » dans l'historique.")
        self.import_id = import_id


class GetImportDetail:
    """Retrouve un import par son identifiant.

    La recherche se fait sur l'historique déjà exposé par le port : inutile d'élargir le
    contrat du lot 3 pour lire un élément d'une liste qu'on sait déjà lire.
    """

    def __init__(self, imports: ImportReadPort) -> None:
        self._imports = imports

    def execute(self, import_id: str) -> ImportRecord:
        for record in self._imports.list_imports():
            if record.import_id == import_id:
                return record

        raise ImportNotFound(import_id)
