"""Fourniture des cas d'utilisation aux routeurs.

Le conteneur est déposé sur `app.state` au démarrage. Les routeurs n'appellent jamais
`build_container` eux-mêmes : ils reçoivent un cas d'utilisation déjà câblé, ce qui rend
chaque routeur testable en injectant des doublures.

`Depends` de FastAPI n'apparaît que dans cette couche.
"""

from __future__ import annotations

from fastapi import Request

from agentscope.application.container import Container
from agentscope.application.use_cases.get_system_status import GetSystemStatus


def provide_container(request: Request) -> Container:
    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - erreur de câblage, pas un cas nominal
        raise RuntimeError(
            "Aucun conteneur n'est attaché à l'application. "
            "L'application doit être construite via create_app(container=...)."
        )
    return container


def provide_get_system_status(request: Request) -> GetSystemStatus:
    return provide_container(request).get_system_status
