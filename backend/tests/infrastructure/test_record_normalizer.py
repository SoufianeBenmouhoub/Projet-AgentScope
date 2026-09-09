from datetime import datetime

from agentscope.application.ports.normalization import NormalizedRecord
from agentscope.infrastructure.normalization.record_normalizer import RecordNormalizer


def test_normalize_session_record():
    record = {
        "conversation_id": "session-123",
        "agent_name": "test-agent",
        "start_time": "2026-09-08T10:30:00+00:00",
        "end_time": "2026-09-08T10:35:00+00:00",
    }

    mapping = {
        "session_id": "conversation_id",
        "agent": "agent_name",
        "started_at": "start_time",
        "ended_at": "end_time",
    }

    normalizer = RecordNormalizer()

    result = normalizer.normalize(
        record=record,
        mapping=mapping,
        source="test-dataset",
    )

    assert isinstance(result, NormalizedRecord)
    assert len(result.sessions) == 1
    assert result.sessions[0].session_id == "session-123"
    assert result.sessions[0].source == "test-dataset"
    assert result.sessions[0].agent == "test-agent"
    assert result.sessions[0].started_at == datetime.fromisoformat("2026-09-08T10:30:00+00:00")
    assert result.sessions[0].ended_at == datetime.fromisoformat("2026-09-08T10:35:00+00:00")
    assert result.model_calls == []
    assert result.tool_calls == []
    assert result.issues == []


def test_missing_session_id_is_reported():
    record = {
        "agent_name": "test-agent",
        "start_time": "2026-09-08T10:30:00+00:00",
    }

    mapping = {
        "session_id": "conversation_id",
        "agent": "agent_name",
        "started_at": "start_time",
        "ended_at": "end_time",
    }

    normalizer = RecordNormalizer()

    result = normalizer.normalize(
        record=record,
        mapping=mapping,
        source="test-dataset",
    )

    assert result.sessions == []
    assert any(issue.field == "session_id" for issue in result.issues)


def test_missing_agent_is_reported():
    record = {
        "conversation_id": "session-123",
        "start_time": "2026-09-08T10:30:00+00:00",
    }

    mapping = {
        "session_id": "conversation_id",
        "agent": "agent_name",
        "started_at": "start_time",
        "ended_at": "end_time",
    }

    normalizer = RecordNormalizer()

    result = normalizer.normalize(
        record=record,
        mapping=mapping,
        source="test-dataset",
    )

    assert result.sessions == []
    assert any(issue.field == "agent" for issue in result.issues)


def test_invalid_datetime_is_reported():
    record = {
        "conversation_id": "session-123",
        "agent_name": "test-agent",
        "start_time": "not-a-date",
    }

    mapping = {
        "session_id": "conversation_id",
        "agent": "agent_name",
        "started_at": "start_time",
        "ended_at": "end_time",
    }

    normalizer = RecordNormalizer()

    result = normalizer.normalize(
        record=record,
        mapping=mapping,
        source="test-dataset",
    )

    assert len(result.sessions) == 1
    assert result.sessions[0].started_at is None
    assert any(issue.field == "started_at" for issue in result.issues)


def test_unmapped_datetime_fields_are_reported_as_missing():
    record = {
        "conversation_id": "session-123",
        "agent_name": "test-agent",
    }

    mapping = {
        "session_id": "conversation_id",
        "agent": "agent_name",
        "started_at": None,
        "ended_at": None,
    }

    normalizer = RecordNormalizer()

    result = normalizer.normalize(
        record=record,
        mapping=mapping,
        source="test-dataset",
    )

    assert len(result.sessions) == 1
    assert result.sessions[0].started_at is None
    assert result.sessions[0].ended_at is None
    assert any(issue.field == "started_at" for issue in result.issues)
    assert any(issue.field == "ended_at" for issue in result.issues)
