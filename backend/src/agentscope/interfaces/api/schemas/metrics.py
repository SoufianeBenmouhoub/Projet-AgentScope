"""Schémas de sortie des indicateurs et des visualisations.

Un point d'attention traverse tout ce module : **une mesure indisponible doit rester
indisponible en JSON**. Elle est transmise avec `value: null` et `available: false`, jamais
convertie en `0`. Sans ça, tout le soin pris dans le domaine serait perdu à la frontière.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from agentscope.domain.metrics.activity import ActivityPoint, ActivitySeries
from agentscope.domain.metrics.aggregation import Aggregate
from agentscope.domain.metrics.breakdown import ToolBreakdown, ToolUsage
from agentscope.domain.metrics.catalog import IndicatorDefinition, IndicatorValue
from agentscope.domain.metrics.filter_options import FilterOptions


class AggregateResponse(BaseModel):
    value: float | None = Field(
        description="Valeur calculée, ou null si la mesure n'est pas disponible. Jamais 0 "
        "pour signifier une absence."
    )
    unit: str
    available: bool = Field(
        description="Faux quand aucune donnée du périmètre ne renseigne la mesure."
    )
    partial: bool = Field(
        description="Vrai quand la valeur ne porte que sur une partie du périmètre."
    )
    covered: int = Field(description="Enregistrements ayant réellement renseigné la mesure.")
    total: int = Field(description="Enregistrements du périmètre.")
    coverage: float | None = Field(
        description="Part couverte, de 0 à 1. Null si le périmètre est vide."
    )

    @classmethod
    def from_domain(cls, aggregate: Aggregate) -> AggregateResponse:
        return cls(
            value=aggregate.value,
            unit=aggregate.unit,
            available=aggregate.is_available,
            partial=aggregate.is_partial,
            covered=aggregate.covered,
            total=aggregate.total,
            coverage=aggregate.coverage,
        )


class IndicatorDefinitionResponse(BaseModel):
    """La définition d'un indicateur, telle qu'elle doit être consultable dans l'interface."""

    key: str
    label: str
    unit: str
    computation: str
    scope: str
    missing_values: str
    comparability: str = Field(
        description="« comparable » ou « source_specific ». Un indicateur propre à une "
        "source ne doit pas être agrégé silencieusement avec les autres."
    )
    kind: str = Field(
        description="« count » ou « measure ». La couverture n'a de sens que pour une "
        "mesure : un dénombrement est complet par construction."
    )

    @classmethod
    def from_domain(cls, definition: IndicatorDefinition) -> IndicatorDefinitionResponse:
        return cls(
            key=definition.key,
            label=definition.label,
            unit=definition.unit,
            computation=definition.computation,
            scope=definition.scope,
            missing_values=definition.missing_values,
            comparability=definition.comparability.value,
            kind=definition.kind.value,
        )


class IndicatorResponse(BaseModel):
    definition: IndicatorDefinitionResponse
    aggregate: AggregateResponse
    sources: list[str]
    mixes_incomparable_sources: bool = Field(
        description="Vrai quand ce chiffre agrège plusieurs sources qui ne le mesurent pas "
        "de la même façon. L'interface doit alors le signaler."
    )

    @classmethod
    def from_domain(cls, indicator: IndicatorValue) -> IndicatorResponse:
        return cls(
            definition=IndicatorDefinitionResponse.from_domain(indicator.definition),
            aggregate=AggregateResponse.from_domain(indicator.aggregate),
            sources=list(indicator.sources),
            mixes_incomparable_sources=indicator.mixes_incomparable_sources,
        )


class KpiSummaryResponse(BaseModel):
    indicators: list[IndicatorResponse]


class IndicatorCatalogResponse(BaseModel):
    """Le catalogue des définitions, consultable même sans aucune donnée importée."""

    definitions: list[IndicatorDefinitionResponse]


class FilterOptionsResponse(BaseModel):
    """Les valeurs sur lesquelles il est possible de filtrer, dérivées des traces importées."""

    sources: list[str]
    agents: list[str]
    models: list[str]
    first_day: date | None = Field(
        description="Première journée observée. Null si aucun enregistrement n'est horodaté."
    )
    last_day: date | None
    is_empty: bool = Field(description="Vrai quand aucune trace n'a été importée.")

    @classmethod
    def from_domain(cls, options: FilterOptions) -> FilterOptionsResponse:
        return cls(
            sources=list(options.sources),
            agents=list(options.agents),
            models=list(options.models),
            first_day=options.first_day,
            last_day=options.last_day,
            is_empty=options.is_empty,
        )


class ToolUsageResponse(BaseModel):
    tool_name: str
    calls: AggregateResponse
    share: AggregateResponse
    error_rate: AggregateResponse
    median_latency: AggregateResponse
    session_ids: list[str] = Field(
        description="Sessions où cet outil apparaît. Permet de revenir du graphique aux "
        "enregistrements correspondants."
    )

    @classmethod
    def from_domain(cls, usage: ToolUsage) -> ToolUsageResponse:
        return cls(
            tool_name=usage.tool_name,
            calls=AggregateResponse.from_domain(usage.calls),
            share=AggregateResponse.from_domain(usage.share),
            error_rate=AggregateResponse.from_domain(usage.error_rate),
            median_latency=AggregateResponse.from_domain(usage.median_latency),
            session_ids=list(usage.session_ids),
        )


class ToolBreakdownResponse(BaseModel):
    usages: list[ToolUsageResponse]
    tool_calls_total: int
    distinct_tools: int

    @classmethod
    def from_domain(cls, breakdown: ToolBreakdown) -> ToolBreakdownResponse:
        return cls(
            usages=[ToolUsageResponse.from_domain(usage) for usage in breakdown.usages],
            tool_calls_total=breakdown.tool_calls_total,
            distinct_tools=breakdown.distinct_tools,
        )


class ActivityPointResponse(BaseModel):
    day: date
    sessions: int
    model_calls: int
    tool_calls: int
    session_ids: list[str]

    @classmethod
    def from_domain(cls, point: ActivityPoint) -> ActivityPointResponse:
        return cls(
            day=point.day,
            sessions=point.sessions,
            model_calls=point.model_calls,
            tool_calls=point.tool_calls,
            session_ids=list(point.session_ids),
        )


class ActivitySeriesResponse(BaseModel):
    points: list[ActivityPointResponse]
    undated_sessions: int = Field(
        description="Sessions sans horodatage, donc absentes de la série. Comptées à part "
        "plutôt que retirées en silence."
    )
    undated_model_calls: int
    undated_tool_calls: int
    has_undated_records: bool

    @classmethod
    def from_domain(cls, series: ActivitySeries) -> ActivitySeriesResponse:
        return cls(
            points=[ActivityPointResponse.from_domain(point) for point in series.points],
            undated_sessions=series.undated_sessions,
            undated_model_calls=series.undated_model_calls,
            undated_tool_calls=series.undated_tool_calls,
            has_undated_records=series.has_undated_records,
        )
