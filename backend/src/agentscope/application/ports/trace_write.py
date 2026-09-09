"""Port d'écriture des traces normalisées."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall


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
c