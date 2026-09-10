"""Regroupement des enregistrements en sessions.

Une ligne d'un fichier de traces est en général **une invocation du modèle**, pas une
session : dans TraceLab, 240 sessions s'étalent sur 15 913 lignes. Le normaliseur produit
une session par enregistrement ; c'est le moteur d'import qui les recolle.

Sans ce regroupement, le tableau de bord afficherait des milliers de sessions d'une seule
invocation, et toute mesure par session — durée, tokens, nombre d'appels — serait fausse.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentscope.application.ports.normalization import NormalizedRecord
from agentscope.application.use_cases.import_traces import ImportTraces
from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.provenance import Provenance
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall

PROVENANCE = Provenance(source="test", filename="traces.jsonl")


class Reader:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def read(self, path: Path, file_format: str | None = None) -> list[dict[str, Any]]:
        return self._records

    def sample(self, path: Path, file_format: str | None = None, limit: int = 100):
        return self._records[:limit]


class Normalizer:
    """Traduit chaque enregistrement de test en une session et ses appels."""

    def normalize(self, record: dict[str, Any], mapping: Any, source: str) -> NormalizedRecord:
        session = Session(
            id=uuid4(),
            external_id=record["session"],
            started_at=record.get("at"),
            ended_at=record.get("at"),
            agent_name=record.get("agent"),
            status=None,
            provenance=PROVENANCE,
        )
        model_call = ModelCall(
            id=uuid4(),
            session_id=session.id,
            external_id=None,
            model_name=None,
            started_at=record.get("at"),
            ended_at=None,
            input_tokens=None,
            output_tokens=None,
            cached_tokens=None,
            status=None,
            provenance=PROVENANCE,
        )
        tool_call = ToolCall(
            id=uuid4(),
            session_id=session.id,
            external_id=None,
            tool_name="Bash",
            started_at=None,
            ended_at=None,
            status=None,
            error=None,
            provenance=PROVENANCE,
        )
        return NormalizedRecord(
            sessions=[session], model_calls=[model_call], tool_calls=[tool_call], issues=[]
        )


class Writer:
    def __init__(self) -> None:
        self.sessions: list[Session] = []
        self.model_calls: list[ModelCall] = []
        self.tool_calls: list[ToolCall] = []
        self.committed = False

    def save_session(self, session: Session) -> None:
        self.sessions.append(session)

    def save_model_call(self, model_call: ModelCall) -> None:
        self.model_calls.append(model_call)

    def save_tool_call(self, tool_call: ToolCall) -> None:
        self.tool_calls.append(tool_call)

    def save_source(self, name: str):
        return uuid4()

    def save_import(self, **_: Any) -> None:
        return None

    def commit(self) -> None:
        self.committed = True


class NeverImported:
    def already_imported(self, file_hash: str) -> bool:
        return False


def run(records: list[dict[str, Any]], tmp_path: Path) -> Writer:
    path = tmp_path / "traces.jsonl"
    path.write_text("contenu", encoding="utf-8")

    writer = Writer()
    ImportTraces(
        file_reader=Reader(records),
        normalizer=Normalizer(),
        trace_writer=writer,
        deduplication=NeverImported(),
    )(path=path, mapping={}, source="test", file_format="jsonl")

    return writer


def at(day: int, hour: int) -> datetime:
    return datetime(2026, 9, day, hour, 0, tzinfo=UTC)


def test_les_enregistrements_dune_meme_session_nen_ecrivent_quune(tmp_path) -> None:
    writer = run(
        [
            {"session": "s1", "at": at(1, 10)},
            {"session": "s1", "at": at(1, 11)},
            {"session": "s1", "at": at(1, 12)},
        ],
        tmp_path,
    )

    assert len(writer.sessions) == 1
    assert writer.sessions[0].external_id == "s1"


def test_des_sessions_distinctes_restent_distinctes(tmp_path) -> None:
    writer = run([{"session": "s1", "at": at(1, 10)}, {"session": "s2", "at": at(1, 11)}], tmp_path)

    assert {session.external_id for session in writer.sessions} == {"s1", "s2"}


def test_les_bornes_de_la_session_couvrent_tous_ses_enregistrements(tmp_path) -> None:
    """Début au plus tôt, fin au plus tard — quel que soit l'ordre des lignes."""
    writer = run(
        [
            {"session": "s1", "at": at(3, 14)},
            {"session": "s1", "at": at(1, 9)},
            {"session": "s1", "at": at(2, 20)},
        ],
        tmp_path,
    )

    assert writer.sessions[0].started_at == at(1, 9)
    assert writer.sessions[0].ended_at == at(3, 14)


def test_un_enregistrement_non_date_ne_retrecit_pas_les_bornes(tmp_path) -> None:
    """Ne pas connaître la date d'une invocation n'apprend rien sur celles des autres."""
    writer = run(
        [{"session": "s1", "at": at(1, 10)}, {"session": "s1", "at": None}],
        tmp_path,
    )

    assert writer.sessions[0].started_at == at(1, 10)
    assert writer.sessions[0].ended_at == at(1, 10)


def test_les_appels_sont_rattaches_a_la_session_regroupee(tmp_path) -> None:
    """C'est le point critique : un appel orphelin serait invisible dans le tableau de bord."""
    writer = run([{"session": "s1", "at": at(1, 10)}, {"session": "s1", "at": at(1, 11)}], tmp_path)

    kept = writer.sessions[0].id
    assert {call.session_id for call in writer.model_calls} == {kept}
    assert {call.session_id for call in writer.tool_calls} == {kept}


def test_un_agent_nomme_par_un_seul_enregistrement_survit_au_regroupement(tmp_path) -> None:
    writer = run(
        [{"session": "s1", "at": at(1, 10)}, {"session": "s1", "at": at(1, 11), "agent": "codex"}],
        tmp_path,
    )

    assert writer.sessions[0].agent_name == "codex"
