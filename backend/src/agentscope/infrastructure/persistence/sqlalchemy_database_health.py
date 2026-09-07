"""Exemple de référence : un adaptateur qui implémente un port."""

from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from agentscope.application.ports.database_health import DatabaseHealthPort


class SqlAlchemyDatabaseHealth(DatabaseHealthPort):
    """Implémentation réelle du port de santé du stockage."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def is_reachable(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True
