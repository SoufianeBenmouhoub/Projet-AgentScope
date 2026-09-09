from uuid import uuid4

from agentscope.application.ports.normalization import (
    NormalizationIssue,
    NormalizedRecord,
)
from agentscope.application.use_cases.import_traces import ImportTraces
from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.provenance import Provenance
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall


class FakeFileReader:
    def __init__(self, records):
        self.records = records
        self.received_path = None
        self.received_format = None

    def read(self, path, file_format=None):
        self.received_path = path
        self.received_format = file_format
        return self.records

    def sample(self, path, file_format=None, limit=100):
        return self.records[:limit]


class FakeNormalizer:
    def __init__(self, normalized):
        self.normalized = normalized
        self.calls = []

    def normalize(self, record, mapping, source):
        self.calls.append(
            {
                "record": record,
                "mapping": mapping,
                "source": source,
            }
        )
        return self.normalized


class FakeTraceWriter:
    def __init__(self):
        self.sessions = []
        self.model_calls = []
        self.tool_calls = []
        self.sources = []
        self.imports = []

    def save_session(self, session):
        self.sessions.append(session)

    def save_model_call(self, model_call):
        self.model_calls.append(model_call)

    def save_tool_call(self, tool_call):
        self.tool_calls.append(tool_call)

    def save_source(self, name):
        source_id = uuid4()
        self.sources.append((name, source_id))
        return source_id

    def save_import(
        self,
        source_id,
        filename,
        file_hash,
        file_format,
        records_imported,
        missing_data_count,
    ):
        self.imports.append(
            {
                "source_id": source_id,
                "filename": filename,
                "file_hash": file_hash,
                "file_format": file_format,
                "records_imported": records_imported,
                "missing_data_count": missing_data_count,
            }
        )

    def commit(self):
        pass


class FakeDeduplication:
    def __init__(self, already_imported=False):
        self._already_imported = already_imported
        self.received_hashes = []

    def already_imported(self, file_hash):
        self.received_hashes.append(file_hash)
        return self._already_imported


def build_normalized_record():
    session_id = uuid4()

    provenance = Provenance(
        source="test-source",
        filename="traces.jsonl",
    )

    session = Session(
        id=session_id,
        external_id="session-1",
        started_at=None,
        ended_at=None,
        agent_name="test-agent",
        status="completed",
        provenance=provenance,
    )

    model_call = ModelCall(
        id=uuid4(),
        session_id=session_id,
        external_id="model-1",
        model_name="test-model",
        started_at=None,
        ended_at=None,
        input_tokens=10,
        output_tokens=20,
        cached_tokens=0,
        status="completed",
        provenance=provenance,
    )

    tool_call = ToolCall(
        id=uuid4(),
        session_id=session_id,
        external_id="tool-1",
        tool_name="test-tool",
        started_at=None,
        ended_at=None,
        status="completed",
        error=None,
        provenance=provenance,
    )

    issue = NormalizationIssue(
        field="agent",
        message="Agent manquant",
    )

    return NormalizedRecord(
        sessions=[session],
        model_calls=[model_call],
        tool_calls=[tool_call],
        issues=[issue],
    )


def test_import_traces_orchestre_lecture_normalisation_et_ecriture(tmp_path):
    path = tmp_path / "traces.jsonl"
    path.write_text("test data", encoding="utf-8")

    normalized = build_normalized_record()

    reader = FakeFileReader(
        [
            {"id": 1},
            {"id": 2},
        ]
    )

    normalizer = FakeNormalizer(normalized)
    writer = FakeTraceWriter()
    deduplication = FakeDeduplication()

    importer = ImportTraces(
        file_reader=reader,
        normalizer=normalizer,
        trace_writer=writer,
        deduplication=deduplication,
    )

    mapping = {
        "session_id": "id",
        "agent": None,
    }

    result = importer(
        path=path,
        mapping=mapping,
        source="test-source",
        file_format="jsonl",
    )

    assert result.records_read == 2
    assert result.sessions_written == 2
    assert result.model_calls_written == 2
    assert result.tool_calls_written == 2

    assert result.issues == (
        normalized.issues[0],
        normalized.issues[0],
    )

    assert reader.received_path == path
    assert reader.received_format == "jsonl"

    assert len(normalizer.calls) == 2
    assert normalizer.calls[0]["record"] == {"id": 1}
    assert normalizer.calls[1]["record"] == {"id": 2}

    assert normalizer.calls[0]["mapping"] == mapping
    assert normalizer.calls[0]["source"] == "test-source"

    assert len(writer.sessions) == 2
    assert len(writer.model_calls) == 2
    assert len(writer.tool_calls) == 2

    assert len(writer.sources) == 1
    assert writer.sources[0][0] == "test-source"

    assert len(writer.imports) == 1
    assert writer.imports[0]["filename"] == "traces.jsonl"
    assert writer.imports[0]["file_format"] == "jsonl"
    assert writer.imports[0]["records_imported"] == 2
    assert writer.imports[0]["missing_data_count"] == 2

    assert len(deduplication.received_hashes) == 1
    assert len(deduplication.received_hashes[0]) == 64


def test_import_traces_refuse_un_fichier_deja_importe(tmp_path):
    path = tmp_path / "traces.jsonl"
    path.write_text("test data", encoding="utf-8")

    normalized = build_normalized_record()

    reader = FakeFileReader(
        [
            {"id": 1},
        ]
    )

    normalizer = FakeNormalizer(normalized)
    writer = FakeTraceWriter()
    deduplication = FakeDeduplication(
        already_imported=True,
    )

    importer = ImportTraces(
        file_reader=reader,
        normalizer=normalizer,
        trace_writer=writer,
        deduplication=deduplication,
    )

    result = importer(
        path=path,
        mapping={"session_id": "id"},
        source="test-source",
        file_format="jsonl",
    )

    assert result.records_read == 0
    assert result.sessions_written == 0
    assert result.model_calls_written == 0
    assert result.tool_calls_written == 0
    assert result.issues == ()
    assert result.already_imported is True

    assert len(deduplication.received_hashes) == 1
    assert len(deduplication.received_hashes[0]) == 64

    assert normalizer.calls == []
    assert reader.received_path is None

    assert writer.sessions == []
    assert writer.model_calls == []
    assert writer.tool_calls == []
    assert writer.sources == []
    assert writer.imports == []
