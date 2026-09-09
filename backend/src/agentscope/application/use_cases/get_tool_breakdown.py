"""Répartition des appels d'outils sur le périmètre filtré."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from agentscope.application.ports.trace_read import ToolCallRecord, TraceFilter, TraceReadPort
from agentscope.domain.metrics.aggregation import count_of, median_of, rate_of
from agentscope.domain.metrics.breakdown import ToolBreakdown, ToolUsage

#: Libellé des appels dont l'outil n'est pas nommé. Ils sont regroupés sous une entrée qui
#: dit son ignorance plutôt que d'être répartis sous un nom inventé ou passés sous silence.
UNNAMED_TOOL = "outil non renseigné"


class GetToolBreakdown:
    """Ordonne les outils du plus utilisé au moins utilisé, avec de quoi y revenir.

    Chaque entrée porte les identifiants des sessions concernées : c'est ce qui permet de
    cliquer sur une barre et de retrouver les enregistrements correspondants.
    """

    def __init__(self, traces: TraceReadPort) -> None:
        self._traces = traces

    def execute(self, filters: TraceFilter) -> ToolBreakdown:
        tool_calls = self._traces.tool_calls(filters)

        grouped: dict[str, list[ToolCallRecord]] = defaultdict(list)
        for call in tool_calls:
            grouped[call.tool_name or UNNAMED_TOOL].append(call)

        usages = tuple(
            sorted(
                (_usage(name, calls, len(tool_calls)) for name, calls in grouped.items()),
                key=lambda usage: (-(usage.calls.value or 0), usage.tool_name),
            )
        )

        return ToolBreakdown(usages=usages, tool_calls_total=len(tool_calls))


def _usage(tool_name: str, calls: Sequence[ToolCallRecord], population: int) -> ToolUsage:
    observed = [call for call in calls if call.is_error is not None]
    failed = [call for call in observed if call.is_error]

    return ToolUsage(
        tool_name=tool_name,
        calls=count_of(len(calls), "appels"),
        share=rate_of(matching=len(calls), observed=population, population=population),
        error_rate=rate_of(
            matching=len(failed),
            observed=len(observed),
            population=len(calls),
        ),
        median_latency=median_of([call.latency_ms for call in calls], "ms"),
        session_ids=tuple(sorted({call.session_id for call in calls})),
    )
