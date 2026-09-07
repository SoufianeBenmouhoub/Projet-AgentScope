"""Tests de règle de domaine : aucune base, aucun serveur, aucun réseau."""

from __future__ import annotations

import pytest

from agentscope.domain.system_status import ComponentState, SystemStatus


def test_une_application_dont_le_stockage_repond_est_operationnelle() -> None:
    status = SystemStatus(version="0.1.0", database=ComponentState.OK)

    assert status.is_operational is True


def test_une_application_privee_de_stockage_nest_pas_operationnelle() -> None:
    status = SystemStatus(version="0.1.0", database=ComponentState.UNAVAILABLE)

    assert status.is_operational is False


def test_un_releve_sans_version_est_refuse() -> None:
    with pytest.raises(ValueError, match="version"):
        SystemStatus(version="   ", database=ComponentState.OK)
