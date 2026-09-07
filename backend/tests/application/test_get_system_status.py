"""Tests de cas d'utilisation : les ports sont remplacés par des doublures."""

from __future__ import annotations

from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.domain.system_status import ComponentState
from tests.fakes.database_health import FakeDatabaseHealth


def test_le_releve_reflete_un_stockage_joignable() -> None:
    use_case = GetSystemStatus(database_health=FakeDatabaseHealth(reachable=True), version="1.2.3")

    status = use_case.execute()

    assert status.database is ComponentState.OK
    assert status.version == "1.2.3"


def test_le_releve_reflete_un_stockage_injoignable() -> None:
    use_case = GetSystemStatus(database_health=FakeDatabaseHealth(reachable=False), version="1.2.3")

    status = use_case.execute()

    assert status.database is ComponentState.UNAVAILABLE
    assert status.is_operational is False


def test_le_port_est_interroge_a_chaque_execution() -> None:
    health = FakeDatabaseHealth()
    use_case = GetSystemStatus(database_health=health, version="1.2.3")

    use_case.execute()
    use_case.execute()

    assert health.calls == 2
