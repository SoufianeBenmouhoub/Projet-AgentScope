"""Port de proposition de mapping par IA.

**C'est le contrat entre le lot 4 (agent IA d'aide à l'import) et le reste de
l'application (UI d'import, moteur d'ingestion).** Le lot 4 le déclare et l'implémente
au-dessus d'un fournisseur IA (Anthropic, Ollama, ou une doublure de test) ; les autres
lots l'utilisent sans connaître le fournisseur choisi.

Deux choix structurants :

1. **L'IA propose, elle n'écrit jamais dans la base.** Ce port renvoie une proposition
   de correspondance entre les champs bruts d'un fichier et les champs attendus par le
   domaine (`SessionRecord`, `ModelCallRecord`, `ToolCallRecord` — voir `trace_read.py`).
   C'est au moteur d'import, après validation par l'utilisateur, d'appliquer la
   transformation.
2. **Une correspondance non trouvée reste explicite.** Un champ cible sans correspondance
   proposée vaut `None`, jamais une supposition — l'ambiguïté doit remonter à
   l'utilisateur plutôt que d'être masquée.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSample:
    """Un champ observé dans le fichier source, avec quelques valeurs d'exemple."""

    name: str
    example_values: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ImportSample:
    """Échantillon soumis à l'agent IA : un aperçu du fichier à importer."""

    source_format: str  # "jsonl", "csv", "parquet"
    fields: tuple[FieldSample, ...]


@dataclass(frozen=True)
class FieldMapping:
    """Correspondance proposée entre un champ cible du domaine et un champ source."""

    target_field: str
    source_field: str | None
    confidence: float | None
    note: str | None = None


@dataclass(frozen=True)
class MappingProposal:
    """Proposition complète de mapping pour un échantillon donné."""

    mappings: tuple[FieldMapping, ...]
    unresolved_notes: tuple[str, ...] = field(default_factory=tuple)


class MappingProposalPort(ABC):
    """Analyse un échantillon et propose une correspondance vers le modèle du domaine."""

    @abstractmethod
    def propose_mapping(self, sample: ImportSample) -> MappingProposal: ...


def build_import_sample(
    records: Sequence[dict[str, object]],
    source_format: str,
    max_examples: int = 3,
) -> ImportSample:
    """Construit un échantillon à partir de quelques enregistrements bruts.

    Récupère l'ensemble des champs observés, avec jusqu'à `max_examples` valeurs
    d'exemple par champ, converties en texte.
    """
    examples_by_field: dict[str, list[str]] = {}
    for record in records:
        for key, value in record.items():
            values = examples_by_field.setdefault(key, [])
            if len(values) < max_examples:
                values.append(str(value))

    fields = tuple(
        FieldSample(name=name, example_values=tuple(values))
        for name, values in examples_by_field.items()
    )
    return ImportSample(source_format=source_format, fields=fields)
