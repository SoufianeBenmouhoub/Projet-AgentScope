"""Tests d'API : l'application est construite avec des doublures, sans base réelle."""

from __future__ import annotations

from tests.interfaces.client import build_client


def test_le_statut_est_expose_quand_tout_repond() -> None:
    response = build_client(database_reachable=True).get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0", "database": "ok", "operational": True}


def test_le_statut_signale_un_stockage_injoignable_sans_echouer() -> None:
    """Une indisponibilité est une information à afficher, pas une erreur 500."""
    response = build_client(database_reachable=False).get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"
    assert response.json()["operational"] is False


def test_le_schema_openapi_est_publie() -> None:
    """C'est ce document qui sert à générer les types TypeScript du front."""
    response = build_client().get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/system/status" in response.json()["paths"]
