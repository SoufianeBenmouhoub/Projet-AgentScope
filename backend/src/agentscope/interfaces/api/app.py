"""Fabrique de l'application FastAPI.

`create_app` reçoit un conteneur déjà câblé au lieu de le construire : c'est ce qui permet
aux tests d'API de tourner avec des doublures, sans base ni service externe.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentscope.application.container import Container
from agentscope.interfaces.api.routers import metrics, sessions, system

DESCRIPTION = (
    "Exploration normalisée de traces d'agents de développement IA : importer, vérifier, "
    "normaliser, explorer."
)


def create_app(
    *,
    container: Container,
    cors_origins: Sequence[str] = (),
    version: str = "0.1.0",
) -> FastAPI:
    app = FastAPI(title="AgentScope", description=DESCRIPTION, version=version)
    app.state.container = container

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(system.router)
    app.include_router(metrics.router)
    app.include_router(sessions.router)

    return app
