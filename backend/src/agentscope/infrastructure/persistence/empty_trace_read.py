"""Implémentation d'attente du port de lecture des traces.

Tant que le lot 2 n'a pas livré le stockage, l'application n'a aucune trace à lire. Cette
implémentation le dit honnêtement : elle ne renvoie aucun enregistrement. Le dashboard
affichera donc « aucune donnée importée » plutôt que des chiffres fabriqués — l'énoncé
interdit explicitement d'alimenter les tableaux de bord avec des données artificielles.

**Son remplacement tiendra en une ligne de `composition.py`.** Aucun cas d'utilisation,
aucune route et aucun composant du front n'aura à changer : c'est précisément ce que la
séparation en couches est censée rendre possible, et ce sera vérifiable ici.
"""

from __future__ import annotations

from collections.abc import Sequence

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFilter,
    TraceReadPort,
)


class EmptyTraceRead(TraceReadPort):
    def sessions(self, filters: TraceFilter) -> Sequence[SessionRecord]:
        return ()

    def model_calls(self, filters: TraceFilter) -> Sequence[ModelCallRecord]:
        return ()

    def tool_calls(self, filters: TraceFilter) -> Sequence[ToolCallRecord]:
        return ()
