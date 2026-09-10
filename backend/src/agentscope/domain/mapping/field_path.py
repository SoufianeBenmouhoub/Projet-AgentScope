"""Résolution d'un champ dans un enregistrement, y compris imbriqué.

Les traces réelles ne sont pas plates. Dans TraceLab, les appels d'outils vivent dans un
tableau `tools[]` et les horodatages dans `timing_events[]` : un mapping qui n'associerait
que des noms de champs de premier niveau ne pourrait rien en extraire.

La syntaxe reste volontairement minuscule — un point pour descendre, des crochets pour
choisir un élément :

    provider
    timing_events[0].timestamp
    tools

Elle est **déclarative et fermée** : aucun code fourni par un modèle n'est exécuté, et un
chemin qui ne mène nulle part rend `None` plutôt que d'échouer. Une donnée absente est un
résultat, pas une panne.
"""

from __future__ import annotations

import re
from typing import Any

_SEGMENT = re.compile(r"^([^\[\]]*)((?:\[\d+\])*)$")
_INDEX = re.compile(r"\[(\d+)\]")


class InvalidFieldPath(ValueError):
    """Le chemin ne respecte pas la syntaxe acceptée."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Chemin « {path} » invalide : {reason}")
        self.path = path


def resolve(record: Any, path: str) -> Any:
    """Suit le chemin dans l'enregistrement, ou rend `None` s'il ne mène nulle part."""
    current = record

    for segment in path.split("."):
        match = _SEGMENT.match(segment)
        if match is None:
            raise InvalidFieldPath(path, f"segment « {segment} » mal formé")

        name, indexes = match.groups()

        if name:
            if not isinstance(current, dict):
                return None
            current = current.get(name)

        for index in _INDEX.findall(indexes):
            if not isinstance(current, list | tuple):
                return None
            position = int(index)
            if position >= len(current):
                return None
            current = current[position]

        if current is None:
            return None

    return current


def validate(path: str) -> None:
    """Vérifie la syntaxe d'un chemin sans avoir besoin d'un enregistrement.

    Sert à refuser un mapping mal formé **avant** d'importer quoi que ce soit, plutôt que
    de découvrir le problème à la millième ligne.
    """
    if not path or not path.strip():
        raise InvalidFieldPath(path, "il est vide")

    for segment in path.split("."):
        if _SEGMENT.match(segment) is None:
            raise InvalidFieldPath(path, f"segment « {segment} » mal formé")
        if not segment.strip():
            raise InvalidFieldPath(path, "il contient un segment vide")
