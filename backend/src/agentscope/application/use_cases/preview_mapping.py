"""Cas d'utilisation : montrer ce qu'un mapping produirait, sans rien écrire.

C'est l'étape qui manque entre « l'IA propose » et « on importe ». Sans elle, la seule
façon de savoir si un mapping est juste est de lancer l'import et de regarder la base — et
de la nettoyer quand il ne l'était pas.

Deux questions sont posées en même temps, parce qu'elles ne se répondent pas l'une l'autre :

1. **Chaque champ vise-t-il la bonne colonne ?** On montre les valeurs réellement lues sur
   l'échantillon. Un chemin qui pointe à côté rend une colonne de vides ; un chemin qui
   pointe sur la mauvaise colonne rend des valeurs qui ne ressemblent pas à ce qu'on
   attend. Les deux se voient d'un coup d'œil, ce qu'aucun compteur ne remplace.
2. **Qu'est-ce que l'import produirait ?** On fait tourner le vrai normaliseur sur
   l'échantillon : sessions, appels, anomalies et refus. Utiliser le normaliseur réel plutôt
   qu'une imitation est le seul moyen que l'aperçu et l'import ne divergent pas.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agentscope.application.ports.normalization import RecordNormalizerPort
from agentscope.domain.mapping.contract import TARGET_FIELDS, validate_mapping
from agentscope.domain.mapping.field_path import resolve

#: Nombre de valeurs d'exemple montrées par champ. Assez pour reconnaître une colonne,
#: assez peu pour que le tableau reste lisible.
EXAMPLES_PER_FIELD = 3


@dataclass(frozen=True)
class FieldOutcome:
    """Ce qu'un champ du modèle donnerait sur l'échantillon."""

    target_field: str
    path: str | None
    scope: str
    required: bool
    examples: tuple[str, ...]
    resolved: int
    """Nombre d'enregistrements de l'échantillon où le chemin mène à une valeur."""

    total: int


@dataclass(frozen=True)
class MappingPreview:
    """Le résultat complet d'un essai à blanc."""

    fields: tuple[FieldOutcome, ...]
    records: int
    sessions: int
    model_calls: int
    tool_calls: int
    issues: tuple[str, ...]
    rejected: int


@dataclass(frozen=True)
class PreviewMapping:
    """Applique un mapping à un échantillon et rend ce qu'il produirait."""

    normalizer: RecordNormalizerPort

    def __call__(
        self, records: Sequence[dict[str, Any]], mapping: dict[str, str | None], source: str = ""
    ) -> MappingPreview:
        """Lève `InvalidMapping` ou `InvalidFieldPath` si le mapping est inapplicable.

        La validation vient d'abord : montrer un aperçu construit avec un mapping que
        l'import refusera ensuite serait la pire des réponses.
        """
        validate_mapping(mapping)

        session_ids: set[str] = set()
        model_calls = 0
        tool_calls = 0
        issues: list[str] = []
        rejected = 0

        for record in records:
            normalized = self.normalizer.normalize(record=record, mapping=mapping, source=source)

            if not normalized.sessions:
                rejected += 1
            for session in normalized.sessions:
                session_ids.add(session.external_id or str(session.id))

            model_calls += len(normalized.model_calls)
            tool_calls += len(normalized.tool_calls)
            issues.extend(f"{issue.field} : {issue.message}" for issue in normalized.issues)

        return MappingPreview(
            fields=tuple(_outcome(field, mapping, records) for field in TARGET_FIELDS),
            records=len(records),
            sessions=len(session_ids),
            model_calls=model_calls,
            tool_calls=tool_calls,
            # Les anomalies se répètent à l'identique d'un enregistrement à l'autre : les
            # lister toutes noierait l'information dans sa propre répétition.
            issues=tuple(dict.fromkeys(issues)),
            rejected=rejected,
        )


def _outcome(field: Any, mapping: dict[str, str | None], records: Sequence[dict[str, Any]]):
    path = mapping.get(field.key)
    examples: list[str] = []
    resolved = 0

    for record in records:
        value = None if path is None else resolve(record, path)
        if value is None:
            continue
        resolved += 1
        if len(examples) < EXAMPLES_PER_FIELD:
            examples.append(_short(value))

    return FieldOutcome(
        target_field=field.key,
        path=path,
        scope=field.scope.value,
        required=field.required,
        examples=tuple(examples),
        resolved=resolved,
        total=len(records),
    )


def _short(value: Any) -> str:
    """Une valeur d'exemple, tronquée : un tableau d'appels d'outils entier ne se lit pas."""
    text = str(value)
    return text if len(text) <= 80 else f"{text[:80]}…"
