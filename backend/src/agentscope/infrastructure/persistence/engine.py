"""Construction du moteur SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine


def build_engine(database_url: str) -> Engine:
    """Crée le moteur de connexion au stockage.

    `pool_pre_ping` évite de servir une connexion morte après une coupure de la base, ce qui
    arrive dès qu'on redémarre le conteneur PostgreSQL pendant le développement.
    """
    return create_engine(database_url, pool_pre_ping=True)
