"""Racine de composition.

**Le seul endroit du projet où les implémentations concrètes sont choisies.** Changer de
moteur de stockage ou de fournisseur d'IA se joue ici, en une ligne, sans toucher aux
règles métier.

C'est aussi le seul module, avec `main.py`, autorisé à importer `infrastructure/`.
"""

from __future__ import annotations

from agentscope.application.container import Container
from agentscope.application.use_cases.get_system_status import GetSystemStatus
from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.infrastructure.persistence.engine import build_engine
from agentscope.infrastructure.persistence.sqlalchemy_database_health import (
    SqlAlchemyDatabaseHealth,
)


def build_container(settings: Settings | None = None) -> Container:
    """Câble les cas d'utilisation avec leurs implémentations réelles."""
    settings = settings or get_settings()
    engine = build_engine(settings.database_url)

    return Container(
        get_system_status=GetSystemStatus(
            database_health=SqlAlchemyDatabaseHealth(engine),
            version=settings.app_version,
        ),
    )
