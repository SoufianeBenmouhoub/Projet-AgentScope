"""Calcul de la synthèse d'indicateurs affichée en tête du dashboard."""

from __future__ import annotations

from collections.abc import Sequence

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFilter,
    TraceReadPort,
)
from agentscope.domain.metrics import catalog
from agentscope.domain.metrics.aggregation import count_of, median_of, rate_of, sum_of
from agentscope.domain.metrics.catalog import IndicatorValue


class GetKpiSummary:
    """Produit les indicateurs du périmètre demandé, chacun avec sa définition.

    Le cas d'utilisation orchestre : il va chercher les enregistrements et appelle les
    règles du domaine. Il ne décide ni de ce qu'un indicateur signifie, ni de la façon de
    traiter une valeur absente — ces deux questions appartiennent au domaine.
    """

    def __init__(self, traces: TraceReadPort) -> None:
        self._traces = traces

    def execute(self, filters: TraceFilter) -> tuple[IndicatorValue, ...]:
        sessions = self._traces.sessions(filters)
        model_calls = self._traces.model_calls(filters)
        tool_calls = self._traces.tool_calls(filters)

        sources = _sources_in_scope(sessions, model_calls, tool_calls)

        return (
            IndicatorValue(
                definition=catalog.SESSIONS_TOTAL,
                aggregate=count_of(len(sessions), catalog.SESSIONS_TOTAL.unit),
                sources=sources,
            ),
            IndicatorValue(
                definition=catalog.MODEL_CALLS_TOTAL,
                aggregate=count_of(len(model_calls), catalog.MODEL_CALLS_TOTAL.unit),
                sources=sources,
            ),
            IndicatorValue(
                definition=catalog.INPUT_TOKENS_TOTAL,
                aggregate=sum_of(
                    [call.input_tokens for call in model_calls],
                    catalog.INPUT_TOKENS_TOTAL.unit,
                ),
                sources=sources,
            ),
            IndicatorValue(
                definition=catalog.CACHE_CREATION_TOKENS,
                aggregate=sum_of(
                    [call.cache_creation_tokens for call in model_calls],
                    catalog.CACHE_CREATION_TOKENS.unit,
                ),
                sources=sources,
            ),
            IndicatorValue(
                definition=catalog.TOOL_ERROR_RATE,
                aggregate=_tool_error_rate(tool_calls),
                sources=sources,
            ),
            IndicatorValue(
                definition=catalog.TOOL_LATENCY_MEDIAN,
                aggregate=median_of(
                    [call.latency_ms for call in tool_calls],
                    catalog.TOOL_LATENCY_MEDIAN.unit,
                ),
                sources=sources,
            ),
        )


def _tool_error_rate(tool_calls: Sequence[ToolCallRecord]):
    observed = [call for call in tool_calls if call.is_error is not None]
    failed = [call for call in observed if call.is_error]

    return rate_of(
        matching=len(failed),
        observed=len(observed),
        population=len(tool_calls),
        unit=catalog.TOOL_ERROR_RATE.unit,
    )


def _sources_in_scope(
    sessions: Sequence[SessionRecord],
    model_calls: Sequence[ModelCallRecord],
    tool_calls: Sequence[ToolCallRecord],
) -> tuple[str, ...]:
    names = {record.source for record in sessions}
    names |= {record.source for record in model_calls}
    names |= {record.source for record in tool_calls}
    return tuple(sorted(names))
