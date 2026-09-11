"""La question posée à un modèle, et la relecture de sa réponse.

Deux adaptateurs partagent ce module : Anthropic et Ollama. Ce n'est pas une économie de
lignes, c'est ce qui rend les deux fournisseurs **comparables** — même question, même
lecture de la réponse. Un écart entre leurs propositions vient alors du modèle, et de rien
d'autre.

La liste des champs visés vient du domaine
(:mod:`agentscope.domain.mapping.contract`). Recopiée ici, elle finirait par diverger, et
le modèle proposerait consciencieusement des champs que le moteur d'import refuse.
"""

from __future__ import annotations

import json

from agentscope.application.ports.mapping_proposal import (
    FieldMapping,
    ImportSample,
    MappingProposal,
)
from agentscope.domain.mapping.contract import FIELDS_BY_KEY, TARGET_FIELDS

RESPONSE_SHAPE = (
    '{"mappings": [{"target_field": "...", "source_field": "..." ou null, '
    '"confidence": 0.0, "note": "..."}]}'
)


def build_prompt(sample: ImportSample) -> str:
    """Décrit le fichier observé et les champs à viser, et exige une réponse en JSON."""
    return (
        "Tu aides à intégrer un fichier de traces d'agent de développement IA dans un "
        "modèle commun.\n\n"
        f"Champs présents dans le fichier ({sample.source_format}), avec des valeurs "
        f"réellement observées :\n{_observed(sample)}\n\n"
        f"Champs du modèle commun à renseigner :\n{_targets()}\n\n"
        "Pour chaque champ du modèle, indique le champ source qui lui correspond, ou null "
        "si aucune correspondance fiable n'existe. Une correspondance inventée coûte plus "
        "cher qu'une absence : une mesure que la source ne publie pas doit rester vide, "
        "elle ne doit jamais devenir zéro. Dans le doute, réponds null et dis pourquoi.\n"
        "Un chemin peut descendre dans la structure avec des points et des crochets, par "
        "exemple « timing_events[0].timestamp ».\n"
        "Ajoute un score de confiance entre 0 et 1 et une note d'une phrase en français.\n\n"
        f"Réponds UNIQUEMENT avec un JSON de cette forme, sans texte autour :\n"
        f"{RESPONSE_SHAPE}"
    )


def _normalized_source_field(value: object) -> object:
    """Un modèle écrit parfois le mot "null" plutôt que la valeur JSON.

    Les traiter différemment laisserait passer un nom de champ inventé sans jamais
    apparaître dans les notes non résolues — exactement ce que cette normalisation
    évite.
    """
    if isinstance(value, str) and value.strip().lower() in ("null", "none", ""):
        return None
    return value


def parse_proposal(raw: str | None) -> MappingProposal:
    """Relit la réponse du modèle sans jamais laisser passer une invention.

    Trois défenses, dans l'ordre où elles servent : le JSON peut être noyé dans du texte
    d'accompagnement, il peut être illisible, et il peut viser un champ qui n'existe pas
    dans le contrat. Aucun de ces cas ne doit produire une proposition silencieusement
    fausse — chacun se voit dans les notes.
    """
    try:
        data = json.loads(_json_part(raw or ""))
        items = data["mappings"]
        proposed = tuple(
            FieldMapping(
                target_field=str(item["target_field"]),
                source_field=_normalized_source_field(item.get("source_field")),
                confidence=item.get("confidence"),
                note=item.get("note"),
            )
            for item in items
        )
    except (json.JSONDecodeError, AttributeError, KeyError, TypeError) as error:
        return MappingProposal(
            mappings=(),
            unresolved_notes=(f"Réponse IA non exploitable : {error}",),
        )

    mappings = tuple(item for item in proposed if item.target_field in FIELDS_BY_KEY)
    invented = tuple(
        f"{item.target_field} : champ hors du modèle commun, proposition ignorée."
        for item in proposed
        if item.target_field not in FIELDS_BY_KEY
    )
    unresolved = tuple(
        f"{item.target_field} : {item.note}"
        for item in mappings
        if item.source_field is None and item.note
    )
    return MappingProposal(mappings=mappings, unresolved_notes=unresolved + invented)


def _observed(sample: ImportSample) -> str:
    return "\n".join(
        f"- {field.name} : exemples = {list(field.example_values)}" for field in sample.fields
    )


def _targets() -> str:
    return "\n".join(
        f"- {field.key}{' (obligatoire)' if field.required else ''} : {field.description}"
        for field in TARGET_FIELDS
    )


def _json_part(raw: str) -> str:
    """Isole l'objet JSON d'une réponse qui l'aurait entouré de texte ou de balises.

    Un modèle à qui l'on demande « uniquement du JSON » répond souvent par un bloc de code
    ou une phrase d'introduction. Refuser la réponse pour cette raison seule gaspillerait
    une proposition par ailleurs correcte.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    return raw[start : end + 1] if start != -1 and end > start else raw
