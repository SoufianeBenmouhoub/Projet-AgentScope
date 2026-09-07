"""Règles d'agrégation des mesures.

**Règle centrale du projet : une donnée indisponible ne devient jamais un zéro.**

Les traces ne renseignent pas les mêmes champs selon l'agent qui les a produites. Sommer
naïvement une colonne partiellement vide produit un chiffre qui a l'air juste et qui est
faux. Toutes les fonctions de ce module distinguent donc trois situations :

- la mesure est renseignée partout : la valeur est exacte ;
- elle est renseignée en partie : la valeur porte sur les enregistrements qui la
  renseignent, et la couverture le dit ;
- elle n'est renseignée nulle part : la valeur est `None`, jamais `0`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median as _median


@dataclass(frozen=True)
class Aggregate:
    """Résultat d'une agrégation, accompagné de son périmètre réel.

    `value` à `None` signifie « non calculable sur ce périmètre » — jamais « zéro ».
    `covered` est le nombre d'enregistrements ayant réellement renseigné la mesure,
    `total` le nombre d'enregistrements du périmètre.
    """

    value: float | None
    unit: str
    covered: int
    total: int

    def __post_init__(self) -> None:
        if self.covered < 0 or self.total < 0:
            raise ValueError("Une couverture ne peut pas être négative.")
        if self.covered > self.total:
            raise ValueError(
                "Une agrégation ne peut pas couvrir plus d'enregistrements qu'il n'y en a "
                f"dans le périmètre ({self.covered} > {self.total})."
            )

    @property
    def is_available(self) -> bool:
        return self.value is not None

    @property
    def coverage(self) -> float | None:
        """Part des enregistrements du périmètre qui renseignent la mesure, de 0 à 1.

        `None` quand le périmètre est vide : une couverture n'a pas de sens sur rien.
        """
        if self.total == 0:
            return None
        return self.covered / self.total

    @property
    def is_partial(self) -> bool:
        """La valeur ne porte-t-elle que sur une partie du périmètre ?"""
        return self.is_available and self.covered < self.total


def _present(values: Sequence[float | None]) -> list[float]:
    return [float(value) for value in values if value is not None]


def sum_of(values: Sequence[float | None], unit: str) -> Aggregate:
    """Somme des valeurs renseignées.

    Aucune valeur renseignée donne `None`, pas `0` : on ne sait pas, on ne prétend pas.
    """
    present = _present(values)
    return Aggregate(
        value=sum(present) if present else None,
        unit=unit,
        covered=len(present),
        total=len(values),
    )


def median_of(values: Sequence[float | None], unit: str) -> Aggregate:
    """Médiane des valeurs renseignées.

    La médiane est préférée à la moyenne partout où la distribution a une queue longue —
    durées de session, latences d'outils. Une moyenne y est tirée par quelques valeurs
    extrêmes et ne décrit plus rien.
    """
    present = _present(values)
    return Aggregate(
        value=float(_median(present)) if present else None,
        unit=unit,
        covered=len(present),
        total=len(values),
    )


def count_of(quantity: int, unit: str) -> Aggregate:
    """Dénombrement.

    Un dénombrement est toujours disponible : zéro session observée, c'est réellement
    zéro, pas une information manquante. C'est la seule famille d'indicateurs où `0` est
    une réponse légitime.
    """
    if quantity < 0:
        raise ValueError("Un dénombrement ne peut pas être négatif.")
    return Aggregate(value=float(quantity), unit=unit, covered=quantity, total=quantity)


def rate_of(matching: int, observed: int, population: int, unit: str = "%") -> Aggregate:
    """Proportion, en pourcentage, rapportée aux seuls enregistrements observés.

    `matching` : enregistrements qui vérifient le critère.
    `observed` : enregistrements dont on connaît l'état — le dénominateur.
    `population` : enregistrements du périmètre, y compris ceux dont l'état est inconnu.

    Le dénominateur exclut délibérément les enregistrements sans information : les
    compter reviendrait à les traiter comme des « non », ce qui fausse le taux vers le bas.
    """
    if matching < 0 or observed < 0:
        raise ValueError("Un dénombrement ne peut pas être négatif.")
    if matching > observed:
        raise ValueError(
            f"Il ne peut pas y avoir plus de cas vérifiant le critère ({matching}) que "
            f"de cas observés ({observed})."
        )
    if observed == 0:
        return Aggregate(value=None, unit=unit, covered=0, total=population)
    return Aggregate(
        value=100.0 * matching / observed,
        unit=unit,
        covered=observed,
        total=population,
    )
