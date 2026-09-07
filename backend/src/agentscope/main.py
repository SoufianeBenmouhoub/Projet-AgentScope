"""Point d'entrée de l'application.

    uvicorn agentscope.main:app --reload

C'est le seul module, avec `composition.py`, qui connaît à la fois la configuration réelle,
l'infrastructure et l'interface HTTP. Tout le reste du projet en est isolé.
"""

from __future__ import annotations

from agentscope.composition import build_container
from agentscope.infrastructure.config.settings import get_settings
from agentscope.interfaces.api.app import create_app

_settings = get_settings()

app = create_app(
    container=build_container(_settings),
    cors_origins=_settings.cors_origins,
    version=_settings.app_version,
)
