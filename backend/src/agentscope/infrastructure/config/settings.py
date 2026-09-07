"""Configuration de l'application, lue depuis l'environnement ou un fichier .env.

Aucun identifiant de modèle, aucun point d'accès et aucune clé ne sont écrits en dur dans
le code : ils arrivent tous par ici. Changer de fournisseur d'IA se fait en modifiant
`.env`, sans toucher au moteur d'import ni aux règles métier.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_version: str = "0.1.0"

    database_url: str = "postgresql+psycopg://agentscope:agentscope@localhost:5432/agentscope"

    # Fournisseur d'IA. La valeur par défaut « fake » permet à un clone du dépôt de
    # démarrer et de faire tourner les tests sans aucune clé API.
    ai_provider: str = "fake"
    ai_model: str = ""
    ai_base_url: str | None = None
    ai_api_key: str | None = None

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Retourne la configuration, lue une seule fois par processus."""
    return Settings()
