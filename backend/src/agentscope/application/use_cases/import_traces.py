"""Cas d'utilisation : importer des traces depuis un fichier source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentscope.application.hash_file import calculate_file_hash
from agentscope.application.ports.file_read import FileReadPort
from agentscope.application.ports.import_deduplication import (
    ImportDeduplicationPort,
)
from agentscope.application.ports.normalization import (
    NormalizationIssue,
    RecordNormalizerPort,
)
from agentscope.application.ports.trace_write import TraceWritePort


@dataclass(frozen=True)
class ImportResult:
    """Résultat d'un import de traces."""

    records_read: int
    sessions_written: int
    model_calls_written: int
    tool_calls_written: int
    issues: tuple[NormalizationIssue, ...]
    already_imported: bool = False


@dataclass(frozen=True)
class ImportTraces:
    """Orchestre la lecture, la normalisation et l'écriture des traces."""

    file_reader: FileReadPort
    normalizer: RecordNormalizerPort
    trace_writer: TraceWritePort
    deduplication: ImportDeduplicationPort

    def __call__(
        self,
        path: Path,
        mapping: dict[str, str | None],
        source: str,
        file_format: str | None = None,
    ) -> ImportResult:
        """Importe et normalise les traces du fichier fourni."""

        # 1. Calcul du hash du fichier.
        file_hash = calculate_file_hash(path)

        # 2. Vérification du doublon AVANT toute écriture.
        if self.deduplication.already_imported(file_hash):
            return ImportResult(
                records_read=0,
                sessions_written=0,
                model_calls_written=0,
                tool_calls_written=0,
                issues=(),
                already_imported=True,
            )

        # 3. Lecture du fichier.
        records = self.file_reader.read(path, file_format)

        issues: list[NormalizationIssue] = []
        sessions_written = 0
        model_calls_written = 0
        tool_calls_written = 0

        # 4. Normalisation et écriture des traces.
        for record in records:
            normalized = self.normalizer.normalize(
                record=record,
                mapping=mapping,
                source=source,
            )

            issues.extend(normalized.issues)

            for session in normalized.sessions:
                self.trace_writer.save_session(session)
                sessions_written += 1

            for model_call in normalized.model_calls:
                self.trace_writer.save_model_call(model_call)
                model_calls_written += 1

            for tool_call in normalized.tool_calls:
                self.trace_writer.save_tool_call(tool_call)
                tool_calls_written += 1

        # 5. Enregistrement de la source.
        source_id = self.trace_writer.save_source(source)

        # 6. Enregistrement de l'import avec son hash.
        self.trace_writer.save_import(
            source_id=source_id,
            filename=path.name,
            file_hash=file_hash,
            file_format=file_format or path.suffix.lstrip("."),
            records_imported=len(records),
            missing_data_count=len(issues),
        )

        # 7. Validation de toute la transaction.
        self.trace_writer.commit()

        return ImportResult(
            records_read=len(records),
            sessions_written=sessions_written,
            model_calls_written=model_calls_written,
            tool_calls_written=tool_calls_written,
            issues=tuple(issues),
            already_imported=False,
        )
