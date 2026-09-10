"""Aller-retour des rejets d'import à travers PostgreSQL.

Ce que ces tests vérifient, aucune doublure ne le peut : que le rejet écrit par
l'adaptateur d'écriture est bien celui que l'adaptateur de lecture rend, et que la clé
étrangère vers l'import est satisfaite au moment de l'insertion.

Sans base joignable, ils sont ignorés plutôt que d'échouer. La CI en lance une.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from agentscope.application.ports.trace_write import ImportRejection
from agentscope.infrastructure.config.settings import get_settings
from agentscope.infrastructure.persistence.models import (
    Base,
    Import,
    ModelCall,
    RawRecord,
    Session,
    Source,
    ToolCall,
)
from agentscope.infrastructure.persistence.models import (
    ImportRejection as ImportRejectionModel,
)
from agentscope.infrastructure.persistence.sqlalchemy_import_read import SqlAlchemyImportRead
from agentscope.infrastructure.persistence.sqlalchemy_trace_writer import SQLAlchemyTraceWriter


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
    with DbSession(engine) as session:
        _wipe(session)
        yield session
        _wipe(session)


def _wipe(session: DbSession) -> None:
    """Vide les tables, des feuilles vers les racines : l'ordre suit les clés étrangères."""
    for table in (ToolCall, ModelCall, Session, RawRecord, ImportRejectionModel, Import, Source):
        session.execute(delete(table))
    session.commit()


def _write(engine, rejections: tuple[ImportRejection, ...], *, records_imported: int = 2) -> str:
    """Écrit un import et ses rejets, puis rend l'identifiant de l'import."""
    writer = SQLAlchemyTraceWriter(sessionmaker(bind=engine))
    source_id = writer.save_source("tracelab")
    writer.save_import(
        source_id=source_id,
        filename="extrait.jsonl",
        file_hash=uuid4().hex * 2,
        file_format="jsonl",
        records_imported=records_imported,
        missing_data_count=0,
        rejections=rejections,
    )
    writer.commit()

    return SqlAlchemyImportRead(engine).list_imports()[0].import_id


A_REJECTION = ImportRejection(
    line_number=7,
    reason="session_id : Sans identifiant de session, l'enregistrement ne peut être rattaché.",
    raw_preview='{"who": "claude"}',
)


def test_un_rejet_ecrit_est_relu_a_lidentique(db) -> None:
    import_id = _write(db.get_bind(), (A_REJECTION,))

    rejections = SqlAlchemyImportRead(db.get_bind()).rejections(import_id)

    assert len(rejections) == 1
    assert rejections[0].line_number == 7
    assert "session_id" in rejections[0].reason
    assert rejections[0].raw_preview == '{"who": "claude"}'


def test_le_compteur_de_rejets_suit_ce_qui_est_reellement_conserve(db) -> None:
    """Un compteur qui ne correspond pas à la liste rendrait l'un des deux menteur."""
    import_id = _write(
        db.get_bind(),
        (A_REJECTION, ImportRejection(line_number=19, reason="Autre refus.", raw_preview=None)),
    )
    reader = SqlAlchemyImportRead(db.get_bind())

    record = next(row for row in reader.list_imports() if row.import_id == import_id)

    assert record.rejected_count == 2
    assert len(reader.rejections(import_id)) == 2


def test_les_rejets_sont_rendus_dans_lordre_du_fichier(db) -> None:
    import_id = _write(
        db.get_bind(),
        tuple(
            ImportRejection(line_number=line, reason="Refus.", raw_preview=None)
            for line in (30, 4, 12)
        ),
    )

    rejections = SqlAlchemyImportRead(db.get_bind()).rejections(import_id)

    assert [rejection.line_number for rejection in rejections] == [4, 12, 30]


def test_un_import_sans_rejet_rend_une_liste_vide(db) -> None:
    import_id = _write(db.get_bind(), ())

    assert SqlAlchemyImportRead(db.get_bind()).rejections(import_id) == ()


def test_un_identifiant_mal_forme_ne_fait_pas_echouer_la_lecture(db) -> None:
    """Un identifiant qui n'est pas un UUID désigne un import qui n'existe pas ; le laisser
    partir jusqu'à PostgreSQL produirait une erreur de type, pas une réponse."""
    assert SqlAlchemyImportRead(db.get_bind()).rejections("pas-un-uuid") == ()
