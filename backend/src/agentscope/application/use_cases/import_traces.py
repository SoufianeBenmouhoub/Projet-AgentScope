"""Cas d'utilisation : importer des traces depuis un fichier source."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from uuid import UUID

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
from agentscope.domain.trace.model_call import ModelCall
from agentscope.domain.trace.session import Session
from agentscope.domain.trace.tool_call import ToolCall


def _widen(known: Session, seen: Session) -> Session:
    """Étend les bornes d'une session avec celles d'un nouvel enregistrement.

    Début au plus tôt, fin au plus tard. Une borne absente ne réduit rien : ne pas connaître
    la date d'un enregistrement n'apprend rien sur celles des autres.
    """
    starts = [moment for moment in (known.started_at, seen.started_at) if moment is not None]
    ends = [moment for moment in (known.ended_at, seen.ended_at) if moment is not None]

    return replace(
        known,
        started_at=min(starts) if starts else None,
        ended_at=max(ends) if ends else None,
        agent_name=known.agent_name or seen.agent_name,
        status=known.status or seen.status,
    )


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

        # Une session couvre en général plusieurs enregistrements : le normaliseur en produit
        # une par enregistrement, on les regroupe ici par identifiant externe. Sans ce
        # regroupement, un extrait de 240 sessions en produirait des milliers, chacune
        # réduite à une seule invocation.
        sessions: dict[str, Session] = {}
        model_calls: list[ModelCall] = []
        tool_calls: list[ToolCall] = []

        # 4. Normalisation.
        for record in records:
            normalized = self.normalizer.normalize(
                record=record,
                mapping=mapping,
                source=source,
            )

            issues.extend(normalized.issues)

            #  Le premier enregistrement d'une session fixe son identifiant interne ; les
            #  suivants rattachent leurs appels à celui-là et étendent ses bornes.
            remapped: dict[UUID, UUID] = {}
            for session in normalized.sessions:
                key = session.external_id or str(session.id)
                known = sessions.get(key)

                if known is None:
                    sessions[key] = session
                else:
                    remapped[session.id] = known.id
                    sessions[key] = _widen(known, session)

            model_calls.extend(
                replace(call, session_id=remapped.get(call.session_id, call.session_id))
                for call in normalized.model_calls
            )
            tool_calls.extend(
                replace(call, session_id=remapped.get(call.session_id, call.session_id))
                for call in normalized.tool_calls
            )

        # 5. Écriture, **les sessions d'abord**. Leurs bornes ne sont connues qu'une fois
        # tous les enregistrements parcourus, et un appel écrit avant la session qu'il
        # référence viole la clé étrangère : l'ordre n'est pas une commodité.
        for session in sessions.values():
            self.trace_writer.save_session(session)

        for model_call in model_calls:
            self.trace_writer.save_model_call(model_call)

        for tool_call in tool_calls:
            self.trace_writer.save_tool_call(tool_call)

        sessions_written = len(sessions)
        model_calls_written = len(model_calls)
        tool_calls_written = len(tool_calls)

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
