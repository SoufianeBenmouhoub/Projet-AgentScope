"""Les champs du modèle commun qu'un mapping peut renseigner.

C'est la liste fermée que l'agent IA doit viser, que l'utilisateur corrige, et que le moteur
d'import applique. La déclarer ici — dans le domaine — plutôt que dans le routeur ou dans le
normaliseur évite qu'elle diverge selon l'endroit d'où on la regarde.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentscope.domain.mapping.field_path import validate


class FieldScope(Enum):
    """À quelle partie du modèle un champ appartient."""

    SESSION = "session"
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    COLLECTION = "collection"
    """Le chemin vers un tableau à parcourir, pas une valeur à lire."""


@dataclass(frozen=True)
class TargetField:
    key: str
    scope: FieldScope
    description: str
    required: bool = False


TARGET_FIELDS: tuple[TargetField, ...] = (
    TargetField(
        "session_id",
        FieldScope.SESSION,
        "Identifiant de la session tel que la source le nomme. Plusieurs enregistrements "
        "portant le même identifiant appartiennent à la même session.",
        required=True,
    ),
    TargetField("agent", FieldScope.SESSION, "Nom de l'agent qui a produit la trace."),
    TargetField(
        "session_status", FieldScope.SESSION, "Statut de la session, si la source en publie un."
    ),
    TargetField(
        "occurred_at",
        FieldScope.MODEL_CALL,
        "Horodatage de l'enregistrement. Les bornes d'une session s'en déduisent : début au "
        "plus tôt, fin au plus tard.",
    ),
    TargetField(
        "ended_at", FieldScope.MODEL_CALL, "Fin de l'appel au modèle, si la source la publie."
    ),
    TargetField("model", FieldScope.MODEL_CALL, "Nom du modèle invoqué."),
    TargetField("input_tokens", FieldScope.MODEL_CALL, "Tokens en entrée."),
    TargetField("output_tokens", FieldScope.MODEL_CALL, "Tokens en sortie."),
    TargetField(
        "cache_creation_tokens",
        FieldScope.MODEL_CALL,
        "Tokens facturés à la création d'entrées de cache. Toutes les sources ne publient "
        "pas cette mesure : la laisser vide est une réponse valable.",
    ),
    TargetField("model_call_id", FieldScope.MODEL_CALL, "Identifiant de l'appel dans la source."),
    TargetField(
        "tools",
        FieldScope.COLLECTION,
        "Chemin vers le tableau des appels d'outils. Les champs « tool_… » sont ensuite lus "
        "à l'intérieur de chacun de ses éléments.",
    ),
    TargetField("tool_name", FieldScope.TOOL_CALL, "Nom de l'outil appelé."),
    TargetField("tool_started_at", FieldScope.TOOL_CALL, "Début de l'appel d'outil."),
    TargetField("tool_ended_at", FieldScope.TOOL_CALL, "Fin de l'appel d'outil."),
    TargetField(
        "tool_is_error",
        FieldScope.TOOL_CALL,
        "Issue de l'appel : vrai en cas d'échec, faux en cas de réussite. Laissé vide quand "
        "la source ne la publie pas — « on ne sait pas » n'est pas « réussi ».",
    ),
    TargetField("tool_error", FieldScope.TOOL_CALL, "Message d'erreur, si la source en publie un."),
    TargetField(
        "tool_call_id", FieldScope.TOOL_CALL, "Identifiant de l'appel d'outil dans la source."
    ),
)

FIELDS_BY_KEY = {field.key: field for field in TARGET_FIELDS}
TOOL_FIELDS = tuple(f.key for f in TARGET_FIELDS if f.scope is FieldScope.TOOL_CALL)
REQUIRED_FIELDS = tuple(f.key for f in TARGET_FIELDS if f.required)


class InvalidMapping(ValueError):
    """Le mapping ne peut pas être appliqué, et on dit pourquoi."""


def validate_mapping(mapping: dict[str, str | None]) -> None:
    """Refuse un mapping inapplicable **avant** d'importer quoi que ce soit.

    Un mapping accepté puis appliqué ligne à ligne échouerait à la millième, laissant une
    base à moitié remplie. Les trois refus possibles sont donc énoncés d'emblée, chacun avec
    ce qu'il aurait fallu écrire.
    """
    unknown = sorted(set(mapping) - set(FIELDS_BY_KEY))
    if unknown:
        raise InvalidMapping(
            f"Champs inconnus : {', '.join(unknown)}. "
            f"Champs acceptés : {', '.join(sorted(FIELDS_BY_KEY))}."
        )

    missing = [key for key in REQUIRED_FIELDS if not mapping.get(key)]
    if missing:
        raise InvalidMapping(
            f"Champs obligatoires non renseignés : {', '.join(missing)}. "
            "Sans eux, les enregistrements ne peuvent pas être rattachés à une session."
        )

    for path in mapping.values():
        if path is not None:
            validate(path)

    mapped_tools = [key for key in TOOL_FIELDS if mapping.get(key)]
    if mapped_tools and not mapping.get("tools"):
        raise InvalidMapping(
            f"Les champs {', '.join(mapped_tools)} désignent des appels d'outils, mais le "
            "champ « tools » ne dit pas où les trouver. Renseignez-le avec le chemin du "
            "tableau qui les contient."
        )
