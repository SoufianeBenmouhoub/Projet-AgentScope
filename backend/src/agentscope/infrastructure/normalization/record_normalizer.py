from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from agentscope.application.ports.normalization import (
    NormalizationIssue,
    NormalizedRecord,
    RecordNormalizerPort,
)
from agentscope.domain.trace.provenance import Provenance
from agentscope.domain.trace.session import Session


class RecordNormalizer(RecordNormalizerPort):
    def normalize(
        self, record: dict[str, Any], mapping: dict[str, str | None], source: str
    ) -> NormalizedRecord:
        issues: list[NormalizationIssue] = []
        session_id = self._get_value(record, mapping, "session_id")
        agent = self._get_value(record, mapping, "agent")
        started_at = self._parse_datetime(record, mapping, "started_at", issues)
        ended_at = self._parse_datetime(record, mapping, "ended_at", issues)
        if session_id is None:
            issues.append(NormalizationIssue(field="session_id", message="Valeur manquante."))
        if agent is None:
            issues.append(NormalizationIssue(field="agent", message="Valeur manquante."))
        sessions = (
            [
                Session(
                    id=uuid4(),
                    external_id=str(session_id),
                    started_at=started_at,
                    ended_at=ended_at,
                    agent_name=str(agent),
                    status=None,
                    provenance=Provenance(source=source, filename="imported"),
                )
            ]
            if session_id is not None and agent is not None
            else []
        )
        return NormalizedRecord(sessions=sessions, model_calls=[], tool_calls=[], issues=issues)

    @staticmethod
    def _get_value(
        record: dict[str, Any], mapping: dict[str, str | None], target_field: str
    ) -> Any:
        source_field = mapping.get(target_field)
        return None if source_field is None else record.get(source_field)

    @staticmethod
    def _parse_datetime(
        record: dict[str, Any],
        mapping: dict[str, str | None],
        target_field: str,
        issues: list[NormalizationIssue],
    ) -> datetime | None:
        value = RecordNormalizer._get_value(record, mapping, target_field)
        if value is None:
            issues.append(NormalizationIssue(field=target_field, message="Valeur manquante."))
            return None
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            issues.append(
                NormalizationIssue(
                    field=target_field, message="La valeur doit être une date ISO-8601."
                )
            )
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            issues.append(NormalizationIssue(field=target_field, message="Date invalide."))
            return None
