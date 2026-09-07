"""Le conteneur des cas d'utilisation exposés à l'extérieur.

Il ne référence que des types de la couche application : c'est `composition.py` qui décide
des implémentations concrètes qui les alimentent. C'est ce qui permet à `interfaces/` de
recevoir des cas d'utilisation câblés sans jamais importer `infrastructure/`.

Chaque lot ajoute ici le ou les cas d'utilisation qu'il expose.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.use_cases.get_system_status import GetSystemStatus


@dataclass(frozen=True)
class Container:
    get_system_status: GetSystemStatus
