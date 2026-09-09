"""Catalogue des indicateurs : leur définition, exposée à l'utilisateur.

L'énoncé demande que « chaque indicateur ait une définition accessible : calcul, unité,
périmètre et traitement des valeurs manquantes ». Ces définitions sont donc **des données
du domaine**, pas des commentaires : elles sont servies par l'API et affichées dans
l'interface à côté de chaque chiffre. Il devient impossible de publier un indicateur sans
dire ce qu'il mesure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agentscope.domain.metrics.aggregation import Aggregate


class Comparability(Enum):
    """Un indicateur garde-t-il le même sens d'une source à l'autre ?"""

    COMPARABLE = "comparable"
    """Mesuré de la même façon par toutes les sources : agrégeable sans réserve."""

    SOURCE_SPECIFIC = "source_specific"
    """Renseigné par certaines sources seulement, ou selon des conventions différentes.

    Agréger un tel indicateur sur plusieurs sources produit un chiffre trompeur : il doit
    rester séparé par source, ou être explicitement signalé.
    """


class IndicatorKind(Enum):
    """Un indicateur dénombre-t-il, ou mesure-t-il ?"""

    COUNT = "count"
    """Un dénombrement : toujours disponible, et complet par construction.

    Parler de « couverture » n'a pas de sens pour lui — il n'y a pas d'enregistrement qui
    « ne renseignerait pas » son propre existence.
    """

    MEASURE = "measure"
    """Une mesure lue dans les traces : elle peut manquer, en tout ou en partie.

    C'est la seule famille pour laquelle la couverture est une information utile, et donc
    la seule que le panneau de qualité des données a besoin de détailler.
    """


@dataclass(frozen=True)
class IndicatorDefinition:
    key: str
    label: str
    unit: str
    computation: str
    scope: str
    missing_values: str
    comparability: Comparability
    kind: IndicatorKind = IndicatorKind.MEASURE


SESSIONS_TOTAL = IndicatorDefinition(
    key="sessions_total",
    label="Sessions",
    unit="sessions",
    computation="Nombre de sessions distinctes dans le périmètre filtré.",
    scope="Toutes les sources retenues par les filtres actifs.",
    missing_values=(
        "Aucune : un dénombrement est toujours disponible. Zéro session signifie réellement zéro."
    ),
    comparability=Comparability.COMPARABLE,
    kind=IndicatorKind.COUNT,
)

MODEL_CALLS_TOTAL = IndicatorDefinition(
    key="model_calls_total",
    label="Appels au modèle",
    unit="appels",
    computation="Nombre d'invocations du modèle dans le périmètre filtré.",
    scope="Toutes les sources retenues par les filtres actifs.",
    missing_values="Aucune : un dénombrement est toujours disponible.",
    comparability=Comparability.COMPARABLE,
    kind=IndicatorKind.COUNT,
)

INPUT_TOKENS_TOTAL = IndicatorDefinition(
    key="input_tokens_total",
    label="Tokens en entrée",
    unit="tokens",
    computation=(
        "Somme des tokens d'entrée déclarés par chaque appel au modèle. Ne couvre que "
        "l'entrée : les traces exploitées ne publient pas de compteur de tokens en sortie, "
        "et un total « entrée + sortie » serait donc inventé."
    ),
    scope="Appels au modèle des sources retenues par les filtres actifs.",
    missing_values=(
        "Les appels sans compteur sont exclus de la somme et retirés de la couverture "
        "affichée. Si aucun appel ne renseigne la mesure, l'indicateur est indisponible, "
        "pas nul."
    ),
    comparability=Comparability.COMPARABLE,
)

CACHE_CREATION_TOKENS = IndicatorDefinition(
    key="cache_creation_tokens",
    label="Tokens de création de cache",
    unit="tokens",
    computation="Somme des tokens facturés à la création d'entrées de cache.",
    scope=(
        "Appels au modèle des sources qui publient cette information. Toutes ne le font "
        "pas : ce compteur est propre à certains agents."
    ),
    missing_values=(
        "Une source qui ne publie pas ce compteur n'est pas comptée comme zéro : elle est "
        "absente de la couverture."
    ),
    comparability=Comparability.SOURCE_SPECIFIC,
)

TOOL_ERROR_RATE = IndicatorDefinition(
    key="tool_error_rate",
    label="Taux d'erreur des appels d'outils",
    unit="%",
    computation=("Appels d'outils en erreur, rapportés aux seuls appels dont l'issue est connue."),
    scope="Appels d'outils des sources retenues par les filtres actifs.",
    missing_values=(
        "Les appels dont l'issue n'est pas renseignée sont exclus du dénominateur. Les y "
        "inclure reviendrait à les compter comme des succès et à sous-estimer le taux."
    ),
    comparability=Comparability.COMPARABLE,
)

TOOL_LATENCY_MEDIAN = IndicatorDefinition(
    key="tool_latency_median",
    label="Latence médiane des appels d'outils",
    unit="ms",
    computation=(
        "Médiane des durées d'exécution observées. La médiane est retenue plutôt que la "
        "moyenne : la distribution a une queue longue, et une moyenne y serait tirée par "
        "quelques appels très lents."
    ),
    scope="Appels d'outils dont la durée est mesurée.",
    missing_values=(
        "Les appels sans durée mesurée sont exclus. Aucune durée mesurée rend "
        "l'indicateur indisponible."
    ),
    comparability=Comparability.COMPARABLE,
)

INDICATORS: tuple[IndicatorDefinition, ...] = (
    SESSIONS_TOTAL,
    MODEL_CALLS_TOTAL,
    INPUT_TOKENS_TOTAL,
    CACHE_CREATION_TOKENS,
    TOOL_ERROR_RATE,
    TOOL_LATENCY_MEDIAN,
)

_BY_KEY = {indicator.key: indicator for indicator in INDICATORS}


def definition(key: str) -> IndicatorDefinition:
    try:
        return _BY_KEY[key]
    except KeyError:
        raise KeyError(
            f"Aucun indicateur « {key} » n'est défini. Un indicateur affiché sans "
            "définition n'est pas publiable : ajoute-le à ce catalogue."
        ) from None


@dataclass(frozen=True)
class IndicatorValue:
    """Un indicateur calculé, indissociable de sa définition et de son périmètre."""

    definition: IndicatorDefinition
    aggregate: Aggregate
    sources: tuple[str, ...]

    @property
    def mixes_incomparable_sources(self) -> bool:
        """Ce chiffre agrège-t-il plusieurs sources qui ne le mesurent pas pareil ?

        Quand c'est vrai, l'interface doit le signaler, ou présenter l'indicateur source
        par source.
        """
        return (
            self.definition.comparability is Comparability.SOURCE_SPECIFIC and len(self.sources) > 1
        )
