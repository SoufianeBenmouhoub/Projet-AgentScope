"""Exemple de référence : un cas d'utilisation."""

from __future__ import annotations

from agentscope.application.ports.database_health import DatabaseHealthPort
from agentscope.domain.system_status import ComponentState, SystemStatus


class GetSystemStatus:
    """Compose un relevé de santé à partir de l'état observé des composants.

    Le cas d'utilisation orchestre ; il ne décide pas de ce qu'« opérationnel » veut dire.
    Cette règle-là appartient au domaine (`SystemStatus.is_operational`).
    """

    def __init__(self, database_health: DatabaseHealthPort, version: str) -> None:
        self._database_health = database_health
        self._version = version

    def execute(self) -> SystemStatus:
        reachable = self._database_health.is_reachable()
        database = ComponentState.OK if reachable else ComponentState.UNAVAILABLE

        return SystemStatus(version=self._version, database=database)
