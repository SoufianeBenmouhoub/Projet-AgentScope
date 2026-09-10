"""Normalisation d'un enregistrement source vers le modèle commun.

Piloté par un mapping déclaratif : aucune connaissance d'une source particulière n'est
écrite ici. Ajouter TraceLab, SWE-chat ou un format inconnu se fait en fournissant un
mapping, pas en modifiant ce fichier — c'est ce que l'énoncé demande.

Un enregistrement produit **une session, un appel au modèle, et autant d'appels d'outils que
la source en déclare**. La session porte l'identifiant externe : c'est le moteur d'import qui
regroupe ensuite les enregistrements partageant le même identifiant, car une session couvre
en général plusieurs enregistrements.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from agentscope.application.ports.normalization import (
    NormalizationIssue,
    NormalizedRecord,
    RecordNormalizerPort,
)
from agentscope.domain.mapping.contract import TOOL_FIELDS
from agentscope.domain.mapping.field_path import resolve
from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.provenance import Provenance
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall


class RecordNormalizer(RecordNormalizerPort):
    def normalize(
        self, record: dict[str, Any], mapping: dict[str, str | None], source: str
    ) -> NormalizedRecord:
        issues: list[NormalizationIssue] = []
        provenance = Provenance(source=source, filename="imported")

        session_id = _text(_read(record, mapping, "session_id"))
        if session_id is None:
            issues.append(
                NormalizationIssue(
                    field="session_id",
                    message="Sans identifiant de session, l'enregistrement ne peut être rattaché.",
                )
            )
            return NormalizedRecord(sessions=[], model_calls=[], tool_calls=[], issues=issues)

        occurred_at = _moment(record, mapping, "occurred_at", issues)
        ended_at = _moment(record, mapping, "ended_at", issues)

        session = Session(
            id=uuid4(),
            external_id=session_id,
            started_at=occurred_at,
            ended_at=ended_at or occurred_at,
            agent_name=_text(_read(record, mapping, "agent")),
            status=_text(_read(record, mapping, "session_status")),
            provenance=provenance,
        )

        model_call = ModelCall(
            id=uuid4(),
            session_id=session.id,
            external_id=_text(_read(record, mapping, "model_call_id")),
            model_name=_text(_read(record, mapping, "model")),
            started_at=occurred_at,
            ended_at=ended_at,
            input_tokens=_whole(record, mapping, "input_tokens", issues),
            output_tokens=_whole(record, mapping, "output_tokens", issues),
            cached_tokens=_whole(record, mapping, "cache_creation_tokens", issues),
            status=None,
            provenance=provenance,
        )

        tool_calls = _tool_calls(record, mapping, session.id, provenance, issues)

        return NormalizedRecord(
            sessions=[session],
            model_calls=[model_call],
            tool_calls=tool_calls,
            issues=issues,
        )


def _tool_calls(
    record: dict[str, Any],
    mapping: dict[str, str | None],
    session_id: Any,
    provenance: Provenance,
    issues: list[NormalizationIssue],
) -> list[ToolCall]:
    """Les appels d'outils, lus dans le tableau que le mapping désigne.

    Sans champ « tools », il n'y a rien à parcourir : ce n'est pas une anomalie, seulement
    une source qui ne publie pas ses appels d'outils.
    """
    collection_path = mapping.get("tools")
    if not collection_path or not any(mapping.get(field) for field in TOOL_FIELDS):
        return []

    collection = resolve(record, collection_path)
    if collection is None:
        return []

    if not isinstance(collection, list | tuple):
        issues.append(
            NormalizationIssue(
                field="tools",
                message=f"« {collection_path} » ne désigne pas une liste d'appels d'outils.",
            )
        )
        return []

    calls: list[ToolCall] = []
    for element in collection:
        if not isinstance(element, dict):
            continue
        calls.append(
            ToolCall(
                id=uuid4(),
                session_id=session_id,
                external_id=_text(_read(element, mapping, "tool_call_id")),
                tool_name=_text(_read(element, mapping, "tool_name")),
                started_at=_moment(element, mapping, "tool_started_at", issues),
                ended_at=_moment(element, mapping, "tool_ended_at", issues),
                status=None,
                error=_text(_read(element, mapping, "tool_error")),
                is_error=_flag(_read(element, mapping, "tool_is_error")),
                provenance=provenance,
            )
        )
    return calls


def _read(record: dict[str, Any], mapping: dict[str, str | None], field: str) -> Any:
    path = mapping.get(field)
    return None if path is None else resolve(record, path)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _flag(value: Any) -> bool | None:
    """Trois états : vrai, faux, et **absent**.

    Une source qui ne publie pas l'issue d'un appel ne dit pas qu'il a réussi. Traduire son
    silence en `False` sous-estimerait le taux d'erreur, ce que ce projet refuse.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "oui"}:
            return True
        if lowered in {"false", "0", "no", "non"}:
            return False
    return None


def _whole(
    record: dict[str, Any],
    mapping: dict[str, str | None],
    field: str,
    issues: list[NormalizationIssue],
) -> int | None:
    """Un compteur entier, ou rien.

    Une valeur illisible est signalée puis laissée absente : mieux vaut un indicateur qui se
    déclare partiel qu'un chiffre fabriqué à partir de données qu'on n'a pas su lire.
    """
    value = _read(record, mapping, field)
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value).strip())
    except ValueError:
        issues.append(
            NormalizationIssue(field=field, message=f"« {value} » n'est pas un nombre entier.")
        )
        return None


def _moment(
    record: dict[str, Any],
    mapping: dict[str, str | None],
    field: str,
    issues: list[NormalizationIssue],
) -> datetime | None:
    """Un horodatage ISO-8601, ou rien.

    L'absence n'est pas signalée comme une anomalie : beaucoup de sources ne datent pas tout,
    et le tableau de bord sait compter ce qui n'est pas horodaté. Seule une valeur présente
    mais illisible mérite d'être remontée.
    """
    value = _read(record, mapping, field)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        issues.append(
            NormalizationIssue(field=field, message=f"« {value} » n'est pas une date ISO-8601.")
        )
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        issues.append(
            NormalizationIssue(field=field, message=f"« {value} » n'est pas une date ISO-8601.")
        )
        return None
