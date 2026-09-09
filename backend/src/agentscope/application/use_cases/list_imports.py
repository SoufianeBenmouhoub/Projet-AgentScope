"""Historique des imports, du plus récent au plus ancien."""

from __future__ import annotations

from collections.abc import Sequence

from agentscope.application.ports.import_read import ImportReadPort, ImportRecord


class ListImports:
    """Retourne les opérations d'import, y compris celles partiellement rejetées.

    Un import qui contient des rejets ou des données manquantes reste visible : le masquer
    ferait perdre la provenance des traces et empêcherait de diagnostiquer le résultat.
    """

    def __init__(self, imports: ImportReadPort) -> None:
        self._imports = imports

    def execute(self) -> Sequence[ImportRecord]:
        records = self._imports.list_imports()
        return tuple(
            sorted(
                records,
                key=lambda record: (record.imported_at, record.import_id),
                reverse=True,
            )
        )
