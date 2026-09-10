"""Lecture des traces normalisées depuis PostgreSQL.

C'est l'implémentation réelle de `TraceReadPort`, celle qui remplace `EmptyTraceRead` dès
qu'il y a des données. Aucun cas d'utilisation, aucune route et aucun composant du front
n'a changé pour l'accueillir : seule la ligne de câblage de `composition.py` bouge.

**Trois écarts entre ce que le dashboard attend et ce que le modèle fournit aujourd'hui.**
Ils sont traités ici, explicitement, plutôt que masqués :

1. **`is_error` n'existe pas** sur `tool_calls`. La table porte un `status` en texte libre
   et un `error` textuel, dont aucun ne permet de distinguer « réussi » de « on ne sait
   pas ». L'adaptateur renvoie donc `None`, et le taux d'erreur s'affiche indisponible.
   Déduire l'échec de la présence d'un message d'erreur donnerait un taux de 100 %, ce qui
   serait pire qu'une absence.
2. **La latence n'existe pas** non plus. Elle est dérivée de `ended_at - started_at` quand
   les deux bornes sont renseignées, et reste absente sinon.
3. **`cached_tokens` est repris comme tokens de création de cache**, en attendant
   confirmation. Si la colonne désigne en réalité les tokens *lus* du cache, c'est le
   libellé de l'indicateur qui devra changer, pas cette correspondance.

Ces trois points sont des demandes ouvertes auprès du lot 2. Tant qu'elles ne sont pas
tranchées, l'interface affiche « indisponible » là où l'information manque — ce qui rend le
manque visible au lieu de le combler avec un chiffre inventé.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, time

from sqlalchemy import Engine, Select, select
from sqlalchemy.orm import Session as DbSession

from agentscope.application.ports.trace_read import (
    ModelCallRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFilter,
    TraceReadPort,
)
from agentscope.infrastructure.persistence.models import ModelCall, Session, Source, ToolCall


class SqlAlchemyTraceRead(TraceReadPort):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def sessions(self, filters: TraceFilter) -> Sequence[SessionRecord]:
        statement = select(Session, Source).join(Source, Session.source_id == Source.id)
        statement = _apply_common(statement, filters, moment=Session.started_at)

        with DbSession(self._engine) as db:
            return [
                SessionRecord(
                    session_id=str(session.id),
                    source=source.name,
                    agent=session.agent_name or source.agent_name,
                    started_at=session.started_at,
                    ended_at=session.ended_at,
                )
                for session, source in db.execute(statement).all()
            ]

    def model_calls(self, filters: TraceFilter) -> Sequence[ModelCallRecord]:
        statement = (
            select(ModelCall, Session, Source)
            .join(Session, ModelCall.session_id == Session.id)
            .join(Source, Session.source_id == Source.id)
        )
        statement = _apply_common(statement, filters, moment=ModelCall.started_at)
        if filters.models:
            statement = statement.where(ModelCall.model_name.in_(filters.models))

        with DbSession(self._engine) as db:
            return [
                ModelCallRecord(
                    session_id=str(session.id),
                    source=source.name,
                    agent=session.agent_name or source.agent_name,
                    model=call.model_name,
                    occurred_at=call.started_at,
                    input_tokens=call.input_tokens,
                    output_tokens=call.output_tokens,
                    # Correspondance en attente de confirmation — voir l'en-tête du module.
                    cache_creation_tokens=call.cached_tokens,
                )
                for call, session, source in db.execute(statement).all()
            ]

    def tool_calls(self, filters: TraceFilter) -> Sequence[ToolCallRecord]:
        statement = (
            select(ToolCall, Session, Source)
            .join(Session, ToolCall.session_id == Session.id)
            .join(Source, Session.source_id == Source.id)
        )
        statement = _apply_common(statement, filters, moment=ToolCall.started_at)

        with DbSession(self._engine) as db:
            return [
                ToolCallRecord(
                    session_id=str(session.id),
                    source=source.name,
                    tool_name=call.tool_name,
                    occurred_at=call.started_at,
                    is_error=call.is_error,
                    latency_ms=_latency_ms(call.started_at, call.ended_at),
                )
                for call, session, source in db.execute(statement).all()
            ]


def _apply_common(statement: Select, filters: TraceFilter, moment) -> Select:
    """Applique les filtres communs aux trois lectures.

    Le filtre par période s'appuie sur l'horodatage propre à chaque table, passé en
    paramètre : une session est retenue sur sa date de début, un appel sur la sienne.
    Un enregistrement non horodaté est exclu dès qu'une période est demandée — on ne sait
    pas s'il y appartient, donc on ne l'y compte pas. L'écart reste visible ailleurs, via
    les compteurs d'enregistrements non datés.

    **Les journées sont découpées en UTC.** Les colonnes du modèle portent un fuseau ;
    comparer une borne naïve à une colonne qui en a un laisse la base choisir un fuseau à
    notre place, et le résultat dépendrait alors de la configuration du serveur. Le
    découpage est donc explicite, et il correspond à celui de la courbe d'activité, qui lit
    la journée dans le fuseau des horodatages stockés.
    """
    if filters.sources:
        statement = statement.where(Source.name.in_(filters.sources))
    if filters.agents:
        statement = statement.where(Session.agent_name.in_(filters.agents))
    if filters.session_ids:
        statement = statement.where(Session.id.in_(filters.session_ids))
    if filters.since is not None:
        statement = statement.where(moment >= _start_of_day(filters.since))
    if filters.until is not None:
        statement = statement.where(moment <= _end_of_day(filters.until))
    return statement


def _start_of_day(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


def _end_of_day(day: date) -> datetime:
    return datetime.combine(day, time.max, tzinfo=UTC)


def _latency_ms(started_at: datetime | None, ended_at: datetime | None) -> int | None:
    """Durée d'un appel d'outil, dérivée de ses bornes.

    Absente si l'une des bornes manque, ou si elles sont incohérentes : une durée négative
    ne serait pas une mesure, seulement une erreur de données.
    """
    if started_at is None or ended_at is None or ended_at < started_at:
        return None
    return int((ended_at - started_at).total_seconds() * 1000)
