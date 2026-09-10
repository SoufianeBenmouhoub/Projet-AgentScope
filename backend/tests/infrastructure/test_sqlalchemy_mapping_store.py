"""Aller-retour d'un mapping à travers PostgreSQL.

Ce que ces tests vérifient, aucune doublure ne le peut : que le mapping relu est exactement
celui qu'on a enregistré, y compris ses champs délibérément vides, et que réenregistrer
sous le même nom remplace au lieu d'ajouter.

Sans base joignable, ils sont ignorés plutôt que d'échouer. La CI en lance une.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DbSession

from agentscope.infrastructure.config.settings import get_settings
from agentscope.infrastructure.persistence.models import Base, Mapping
from agentscope.infrastructure.persistence.sqlalchemy_mapping_store import SqlAlchemyMappingStore

A_MAPPING: dict[str, str | None] = {
    "session_id": "session_id",
    "agent": "provider",
    "occurred_at": "timing_events[0].timestamp",
    "cache_creation_tokens": None,
}


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
def store(engine):
    with DbSession(engine) as session:
        session.execute(delete(Mapping))
        session.commit()

    yield SqlAlchemyMappingStore(engine)

    with DbSession(engine) as session:
        session.execute(delete(Mapping))
        session.commit()


def test_un_mapping_enregistre_est_relu_a_lidentique(store) -> None:
    saved = store.save("TraceLab", "tracelab", A_MAPPING)

    relu = store.get(saved.mapping_id)

    assert relu is not None
    assert relu.name == "TraceLab"
    assert relu.source_name == "tracelab"
    assert relu.fields == A_MAPPING


def test_un_champ_delibrement_vide_le_reste(store) -> None:
    """Relire un mapping doit dire ce qui a été écarté, pas seulement ce qui a été rempli.
    Un `null` qui deviendrait une absence perdrait cette information."""
    saved = store.save("TraceLab", None, A_MAPPING)

    assert store.get(saved.mapping_id).fields["cache_creation_tokens"] is None


def test_reenregistrer_sous_le_meme_nom_remplace(store) -> None:
    first = store.save("TraceLab", None, A_MAPPING)
    second = store.save("TraceLab", "autre-source", {"session_id": "autre"})

    assert second.mapping_id == first.mapping_id
    assert second.created_at == first.created_at
    assert second.updated_at > first.updated_at
    assert len(store.list_mappings()) == 1
    assert store.get(first.mapping_id).fields == {"session_id": "autre"}


def test_deux_noms_donnent_deux_mappings(store) -> None:
    store.save("TraceLab", None, A_MAPPING)
    store.save("CSV plat", None, {"session_id": "conversation_id"})

    assert {saved.name for saved in store.list_mappings()} == {"TraceLab", "CSV plat"}


def test_supprime_un_mapping(store) -> None:
    saved = store.save("TraceLab", None, A_MAPPING)

    assert store.delete(saved.mapping_id) is True
    assert store.list_mappings() == ()
    assert store.get(saved.mapping_id) is None


def test_supprimer_ce_qui_nexiste_pas_rend_faux(store) -> None:
    assert store.delete("00000000-0000-0000-0000-000000000000") is False


def test_un_identifiant_mal_forme_ne_fait_pas_echouer_la_lecture(store) -> None:
    """Le laisser partir jusqu'à PostgreSQL produirait une erreur de type, pas une réponse."""
    assert store.get("pas-un-uuid") is None
    assert store.delete("pas-un-uuid") is False
