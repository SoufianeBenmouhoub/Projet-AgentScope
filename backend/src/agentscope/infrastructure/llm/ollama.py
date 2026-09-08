"""Adaptateur Ollama pour le port de proposition de mapping."""

from __future__ import annotations

import json

from openai import OpenAI

from agentscope.application.ports.mapping_proposal import (
    FieldMapping,
    ImportSample,
    MappingProposal,
    MappingProposalPort,
)

TARGET_FIELDS = [
    "session_id",
    "source",
    "agent",
    "started_at",
    "ended_at",
    "model",
    "occurred_at",
    "input_tokens",
    "output_tokens",
    "cache_creation_tokens",
    "tool_name",
    "is_error",
    "latency_ms",
]


class OllamaMappingProposal(MappingProposalPort):
    """Propose un mapping via un modèle exécuté localement avec Ollama."""

    def __init__(self, model: str, base_url: str) -> None:
        self._model = model
        self._client = OpenAI(base_url=base_url, api_key="ollama")

    def propose_mapping(self, sample: ImportSample) -> MappingProposal:
        prompt = self._build_prompt(sample)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_response(response.choices[0].message.content)

    def _build_prompt(self, sample: ImportSample) -> str:
        fields_desc = "\n".join(
            f"- {f.name}: exemples = {list(f.example_values)}" for f in sample.fields
        )
        targets = ", ".join(TARGET_FIELDS)
        return (
            f"Voici les champs trouvés dans un fichier au format {sample.source_format} :\n"
            f"{fields_desc}\n\n"
            f"Pour chaque champ cible parmi [{targets}], propose le champ source qui lui "
            f"correspond le mieux (ou null si aucune correspondance fiable), avec un score "
            f"de confiance entre 0 et 1, et une courte note en français (une phrase) qui "
            f"explique ton choix — en particulier pourquoi aucune correspondance fiable "
            f"n'a été trouvée, le cas échéant.\n"
            f"Réponds UNIQUEMENT avec un JSON de cette forme, sans texte autour :\n"
            f'{{"mappings": [{{"target_field": "...", "source_field": "..." ou null, '
            f'"confidence": 0.0, "note": "..."}}]}}'
        )

    def _parse_response(self, raw: str) -> MappingProposal:
        try:
            data = json.loads(raw)
            mappings = tuple(
                FieldMapping(
                    target_field=item["target_field"],
                    source_field=item.get("source_field"),
                    confidence=item.get("confidence"),
                    note=item.get("note"),
                )
                for item in data.get("mappings", [])
            )
            unresolved_notes = tuple(
                f"{mapping.target_field} : {mapping.note}"
                for mapping in mappings
                if mapping.source_field is None and mapping.note
            )
            return MappingProposal(mappings=mappings, unresolved_notes=unresolved_notes)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            return MappingProposal(
                mappings=(),
                unresolved_notes=(f"Réponse IA non exploitable : {exc}",),
            )
