"""Port d'écriture des traces normalisées."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall


@dataclass(frozen=True)
class ImportRejection:
    """Un enregistrement que l'import n'a pas pu retenir, et pourquoi.

    À ne pas confondre avec une information manquante. Un enregistrement dont un compteur
    est illisible entre quand même en base, amputé de ce compteur ; un enregistrement rejeté
    n'entre pas du tout. Les compter ensemble ferait croire qu'un fichier a été importé en
    entier alors qu'une partie a été écartée.
    """

    line_number: int
    """Rang de l'enregistrement dans le fichier, à partir de 1 — de quoi aller le voir."""

    reason: str
    raw_preview: str | None
    """Début de l'enregistrement d'origine, pour reconnaître ce qui a été refusé."""


class TraceWritePort(ABC):
    """Contrat d'écriture des objets métier normalisés."""

    @abstractmethod
    def save_session(self, session: Session) -> None:
        """Enregistre une session."""
        ...

    @abstractmethod
    def save_model_call(self, model_call: ModelCall) -> None:
        """Enregistre un appel modèle."""
        ...

    @abstractmethod
    def save_tool_call(self, tool_call: ToolCall) -> None:
        """Enregistre un appel outil."""
        ...

    @abstractmethod
    def save_source(self, name: str) -> UUID:
        """Crée ou récupère une source."""
        ...

    @abstractmethod
    def save_import(
        self,
        source_id: UUID,
        filename: str,
        file_hash: str,
        file_format: str,
        records_imported: int,
        missing_data_count: int,
        rejections: Sequence[ImportRejection] = (),
    ) -> None:
        """Enregistre un import, avec le détail de ce qu'il a refusé.

        Les rejets sont passés en entier, pas seulement comptés : un nombre seul dit qu'il
        y a eu un problème sans permettre de le corriger.
        """
        ...

    @abstractmethod
    def commit(self) -> None:
        """Valide la transaction en cours."""
        ...
