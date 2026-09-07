"""Tests d'API : l'application est construite avec des doublures, sans base réelle."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agentscope.application.container import Container
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.interfaces.api.app import create_app
from tests.fakes.database_health import FakeDatabaseHealth


def _client(*, database_reachable: bool) -> TestClient:
    container = Container(
        get_system_status=GetSystemStatus(
            database_health=FakeDatabaseHealth(reachable=database_reachable),
            version="0.1.0",
        ),
    )
    return TestClient(create_app(container=container, version="0.1.0"))


def test_le_statut_est_expose_quand_tout_repond() -> None:
    response = _client(database_reachable=True).get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0", "database": "ok", "operational": True}


def test_le_statut_signale_un_stockage_injoignable_sans_echouer() -> None:
    """Une indisponibilité est une information à afficher, pas une erreur 500."""
    response = _client(database_reachable=False).get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"
    assert response.json()["operational"] is False


def test_le_schema_openapi_est_publie() -> None:
    """C'est ce document qui sert à générer les types TypeScript du front."""
    response = _client(database_reachable=True).get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/system/status" in response.json()["paths"]
