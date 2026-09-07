"""Doublure du port de santé du stockage.

Exemple de référence : c'est ainsi qu'on teste un cas d'utilisation sans base de données.
Chaque lot dépose ici les doublures de ses propres ports — en particulier le lot 4, dont la
doublure d'IA permet de faire tourner toute la suite de tests sans appeler un service réel.
"""

from __future__ import annotations

from agentscope.application.ports.database_health import DatabaseHealthPort


class FakeDatabaseHealth(DatabaseHealthPort):
    def __init__(self, *, reachable: bool = True) -> None:
        self._reachable = reachable
        self.calls = 0

    def is_reachable(self) -> bool:
        self.calls += 1
        return self._reachable
