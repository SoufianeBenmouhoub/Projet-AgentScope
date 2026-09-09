"""Tests de l'adaptateur de lecture PostgreSQL.

Ces tests sont les seuls du projet à exiger une base réelle : ils vérifient précisément la
traduction entre le modèle relationnel et le contrat attendu par le dashboard, ce qu'une
doublure ne peut pas faire. Ils valident donc aussi le schéma du lot 2 contre les besoins
du lot 5.

Sans base joignable, ils sont ignorés plutôt que d'échouer : la suite reste exécutable sans
Docker. La CI, elle, lance un PostgreSQL, donc ils y tournent réellement.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DbSession

from agentscope.application.ports.trace_read import TraceFilter
from agentscope.infrastructure.config.settings import get_settings
from agentscope.infrastructure.persistence.models import (
    Base,
    ModelCall,
    Session,
    Source,
    ToolCall,
)
from agentscope.infrastructure.persistence.sqlalchemy_trace_read import SqlAlchemyTraceRead


@pytest.fixture(scope="module")
def engine():
    candidate = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with candidate.connect():
            pass
    except SQLAlchemyError:
        pytest.skip(
            "Aucune base PostgreSQL joignable. Lancez « docker compose up -d » pour "
            "exécuter ces tests."
        )
    Base.metadata.create_all(candidate)
    return candidate


@pytest.fixture
def db(engine):
    """Une base vide avant chaque test, et laissée vide après."""
    with DbSession(engine) as session:
        _wipe(session)
        yield session
        _wipe(session)


def _wipe(session: DbSession) -> None:
    for table in (ToolCall, ModelCall, Session, Source):
        session.execute(delete(table))
    session.commit()


def _source(db: DbSession, name: str, agent: str | None = "claude-code") -> Source:
    source = Source(id=uuid4(), name=name, agent_name=agent, created_at=datetime(2026, 9, 1))
    db.add(source)
    db.commit()
    return source


def _session(
    db: DbSession,
    source: Source,
    *,
    agent: str | None = None,
    started_at: datetime | None = datetime(2026, 9, 3, 10, 0),
    ended_at: datetime | None = datetime(2026, 9, 3, 10, 30),
) -> Session:
    row = Session(
        id=uuid4(),
        source_id=source.id,
        agent_name=agent,
        started_at=started_at,
        ended_at=ended_at,
    )
    db.add(row)
    db.commit()
    return row


class TestSessions:
    def test_traduit_une_session_vers_le_contrat_du_dashboard(self, db) -> None:
        source = _source(db, "tracelab-claude")
        row = _session(db, source)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(TraceFilter())

        assert len(records) == 1
        assert records[0].session_id == str(row.id)
        assert records[0].source == "tracelab-claude"
        # Les colonnes du modèle portent un fuseau : la base renvoie des horodatages
        # conscients, et le dashboard les manipule tels quels.
        assert records[0].started_at == datetime(2026, 9, 3, 10, 0, tzinfo=UTC)

    def test_le_nom_dagent_de_la_session_prime_sur_celui_de_la_source(self, db) -> None:
        source = _source(db, "tracelab", agent="claude-code")
        _session(db, source, agent="codex")

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(TraceFilter())

        assert records[0].agent == "codex"

    def test_un_agent_inconnu_reste_absent_plutot_que_dinvente(self, db) -> None:
        source = _source(db, "source-anonyme", agent=None)
        _session(db, source, agent=None)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(TraceFilter())

        assert records[0].agent is None

    def test_une_session_sans_horodatage_est_lue_sans_erreur(self, db) -> None:
        source = _source(db, "tracelab")
        _session(db, source, started_at=None, ended_at=None)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(TraceFilter())

        assert records[0].started_at is None


class TestFiltres:
    def test_le_filtre_par_source_restreint_la_lecture(self, db) -> None:
        claude = _source(db, "tracelab-claude")
        codex = _source(db, "tracelab-codex")
        _session(db, claude)
        _session(db, codex)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(
            TraceFilter(sources=("tracelab-claude",))
        )

        assert [record.source for record in records] == ["tracelab-claude"]

    def test_le_filtre_par_periode_retient_les_bornes_incluses(self, db) -> None:
        source = _source(db, "tracelab")
        _session(db, source, started_at=datetime(2026, 9, 3, 23, 59), ended_at=None)
        _session(db, source, started_at=datetime(2026, 9, 9, 0, 1), ended_at=None)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(
            TraceFilter(since=date(2026, 9, 3), until=date(2026, 9, 3))
        )

        assert len(records) == 1

    def test_un_enregistrement_non_horodate_sort_du_perimetre_dune_periode(self, db) -> None:
        """On ne sait pas s'il appartient à la période : on ne l'y compte pas."""
        source = _source(db, "tracelab")
        _session(db, source, started_at=None, ended_at=None)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(
            TraceFilter(since=date(2026, 9, 1), until=date(2026, 9, 30))
        )

        assert records == []

    def test_le_filtre_par_identifiant_ramene_une_session_precise(self, db) -> None:
        source = _source(db, "tracelab")
        first = _session(db, source)
        _session(db, source)

        records = SqlAlchemyTraceRead(db.get_bind()).sessions(
            TraceFilter(session_ids=(str(first.id),))
        )

        assert [record.session_id for record in records] == [str(first.id)]


class TestModelCalls:
    def test_traduit_les_compteurs_de_tokens(self, db) -> None:
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(
            ModelCall(
                id=uuid4(),
                session_id=session.id,
                model_name="claude-opus-5",
                started_at=datetime(2026, 9, 3, 10, 5),
                input_tokens=1200,
                output_tokens=None,
                cached_tokens=300,
            )
        )
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).model_calls(TraceFilter())

        assert records[0].input_tokens == 1200
        assert records[0].cache_creation_tokens == 300
        assert records[0].session_id == str(session.id)

    def test_un_compteur_absent_reste_absent(self, db) -> None:
        """La règle centrale du projet, vérifiée jusqu'au SQL : NULL n'est pas zéro."""
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(ModelCall(id=uuid4(), session_id=session.id, input_tokens=None))
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).model_calls(TraceFilter())

        assert records[0].input_tokens is None

    def test_le_filtre_par_modele_restreint_la_lecture(self, db) -> None:
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(ModelCall(id=uuid4(), session_id=session.id, model_name="claude-opus-5"))
        db.add(ModelCall(id=uuid4(), session_id=session.id, model_name="autre"))
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).model_calls(
            TraceFilter(models=("claude-opus-5",))
        )

        assert [record.model for record in records] == ["claude-opus-5"]


class TestToolCalls:
    def test_derive_la_latence_des_bornes_de_lappel(self, db) -> None:
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(
            ToolCall(
                id=uuid4(),
                session_id=session.id,
                tool_name="bash",
                started_at=datetime(2026, 9, 3, 10, 6, 0),
                ended_at=datetime(2026, 9, 3, 10, 6, 2),
            )
        )
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).tool_calls(TraceFilter())

        assert records[0].latency_ms == 2000

    def test_sans_bornes_completes_la_latence_est_absente(self, db) -> None:
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(ToolCall(id=uuid4(), session_id=session.id, tool_name="bash", ended_at=None))
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).tool_calls(TraceFilter())

        assert records[0].latency_ms is None

    def test_lissue_dun_appel_reste_inconnue_faute_de_colonne(self, db) -> None:
        """Le modèle ne distingue pas encore « réussi » de « on ne sait pas ».

        Déduire l'échec de la présence d'un message d'erreur donnerait un taux d'erreur de
        100 %. Tant que la colonne n'existe pas, l'indicateur s'affiche indisponible — ce
        test tombera le jour où le lot 2 ajoutera `is_error`, et c'est voulu.
        """
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(ToolCall(id=uuid4(), session_id=session.id, tool_name="bash", error="boum"))
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).tool_calls(TraceFilter())

        assert records[0].is_error is None

    def test_un_outil_non_nomme_est_lu_sans_nom_invente(self, db) -> None:
        source = _source(db, "tracelab")
        session = _session(db, source)
        db.add(ToolCall(id=uuid4(), session_id=session.id, tool_name=None))
        db.commit()

        records = SqlAlchemyTraceRead(db.get_bind()).tool_calls(TraceFilter())

        assert records[0].tool_name is None


def test_un_perimetre_vide_ne_produit_aucun_enregistrement(db) -> None:
    reader = SqlAlchemyTraceRead(db.get_bind())

    assert reader.sessions(TraceFilter()) == []
    assert reader.model_calls(TraceFilter()) == []
    assert reader.tool_calls(TraceFilter()) == []
