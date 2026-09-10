"""Contrat de conservation des mappings.

Un mapping mis au point sur un fichier vaut pour tous les fichiers de la même source. Le
redemander à l'agent IA à chaque import, ou le faire ressaisir, reviendrait à jeter le
travail de vérification que l'utilisateur vient de faire.

**Ce qui est conservé, ce sont des correspondances entre champs, pas la proposition d'un
modèle.** Un mapping enregistré reste donc utilisable après un changement de fournisseur ou
de modèle : rien dans ce qu'on stocke ne dépend de qui l'a proposé.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SavedMapping:
    """Un mapping conservé sous un nom, réutilisable tel quel."""

    mapping_id: str
    name: str
    source_name: str | None
    """Source pour laquelle il a été mis au point, quand elle est connue."""

    fields: dict[str, str | None]
    created_at: datetime
    updated_at: datetime


class MappingStorePort(ABC):
    """Conservation et relecture des mappings mis au point par l'utilisateur."""

    @abstractmethod
    def save(
        self, name: str, source_name: str | None, fields: dict[str, str | None]
    ) -> SavedMapping:
        """Conserve un mapping sous ce nom, en remplaçant celui qui le portait déjà.

        Le remplacement est voulu : corriger un mapping consiste à le réenregistrer, et
        laisser s'accumuler « tracelab », « tracelab 2 », « tracelab final » ne rendrait
        service à personne.
        """
        ...

    @abstractmethod
    def list_mappings(self) -> Sequence[SavedMapping]: ...

    @abstractmethod
    def get(self, mapping_id: str) -> SavedMapping | None:
        """Le mapping portant cet identifiant, ou `None` s'il n'existe pas."""
        ...

    @abstractmethod
    def delete(self, mapping_id: str) -> bool:
        """Supprime le mapping ; rend `False` s'il n'existait pas."""
        ...
