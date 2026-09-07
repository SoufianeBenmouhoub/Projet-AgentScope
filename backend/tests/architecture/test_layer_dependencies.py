"""Vérifie mécaniquement le sens des dépendances entre couches.

Ce test est la traduction exécutable de docs/adr/0002-regle-des-couches.md.

Sans lui, la règle des couches ne serait qu'une convention — et une convention finit
toujours par être violée par six personnes fatiguées un jeudi soir. Il tourne dans la CI :
une pull request qui franchit une frontière est rouge, avec un message qui dit laquelle.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

PACKAGE = "agentscope"
SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / PACKAGE

#: Pour chaque couche, les couches du projet qu'elle a le droit d'importer.
#: Une couche peut toujours s'importer elle-même.
ALLOWED_INTERNAL_IMPORTS: dict[str, frozenset[str]] = {
    "domain": frozenset(),
    "application": frozenset({"domain"}),
    "infrastructure": frozenset({"domain", "application"}),
    "interfaces": frozenset({"domain", "application"}),
    "composition": frozenset({"domain", "application", "infrastructure"}),
    "main": frozenset({"domain", "application", "infrastructure", "interfaces", "composition"}),
}

#: Les couches qui n'ont le droit d'utiliser que la bibliothèque standard.
LAYERS_WITHOUT_EXTERNAL_DEPENDENCIES = frozenset({"domain", "application"})

RULES_REFERENCE = "Voir CONTRIBUTING.md § 2 et docs/adr/0002-regle-des-couches.md."


def _discover_modules() -> list[tuple[Path, str]]:
    """Associe chaque module source à sa couche."""
    modules: list[tuple[Path, str]] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        relative = path.relative_to(SOURCE_ROOT)
        if len(relative.parts) == 1:
            if relative.stem == "__init__":
                continue
            layer = relative.stem
        else:
            layer = relative.parts[0]
        modules.append((path, layer))
    return modules


def _module_id(path: Path) -> str:
    return path.relative_to(SOURCE_ROOT).as_posix()


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _absolute_imports(path: Path) -> list[tuple[str, int]]:
    """Retourne les modules importés en absolu, avec leur numéro de ligne."""
    imported: list[tuple[str, int]] = []
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Import):
            imported.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.append((node.module, node.lineno))
    return imported


MODULES = _discover_modules()
MODULE_IDS = [_module_id(path) for path, _ in MODULES]

PURE_MODULES = [item for item in MODULES if item[1] in LAYERS_WITHOUT_EXTERNAL_DEPENDENCIES]
PURE_MODULE_IDS = [_module_id(path) for path, _ in PURE_MODULES]


def test_les_sources_sont_trouvees_et_chaque_couche_a_une_regle() -> None:
    """Garde-fou du garde-fou : sans lui, un chemin cassé rendrait tous les tests verts."""
    assert MODULES, f"Aucun module Python trouvé sous {SOURCE_ROOT}."

    undeclared = sorted({layer for _, layer in MODULES} - set(ALLOWED_INTERNAL_IMPORTS))
    assert not undeclared, (
        f"Ces couches existent dans le code mais n'ont aucune règle déclarée : {undeclared}. "
        "Ajouter une couche est une décision d'architecture : déclare ses dépendances "
        f"autorisées dans ce fichier et documente-la. {RULES_REFERENCE}"
    )


@pytest.mark.parametrize(("path", "layer"), MODULES, ids=MODULE_IDS)
def test_les_dependances_vont_vers_l_interieur(path: Path, layer: str) -> None:
    allowed = ALLOWED_INTERNAL_IMPORTS[layer]

    for module, lineno in _absolute_imports(path):
        if not module.startswith(f"{PACKAGE}."):
            continue

        target = module.split(".")[1]
        if target == layer or target in allowed:
            continue

        pytest.fail(
            f"{_module_id(path)}:{lineno} — la couche « {layer} » importe « {target} » "
            f"({module}), ce qui n'est pas autorisé.\n"
            f"Couches importables depuis « {layer} » : {sorted(allowed) or 'aucune'}.\n"
            "Si le besoin est réel, la réponse est presque toujours de déclarer un port "
            f"dans application/ports/ et de l'implémenter dans infrastructure/. {RULES_REFERENCE}"
        )


@pytest.mark.parametrize(("path", "layer"), PURE_MODULES, ids=PURE_MODULE_IDS)
def test_le_coeur_metier_na_aucune_dependance_externe(path: Path, layer: str) -> None:
    for module, lineno in _absolute_imports(path):
        root = module.split(".")[0]
        if root == PACKAGE or root in sys.stdlib_module_names:
            continue

        pytest.fail(
            f"{_module_id(path)}:{lineno} — la couche « {layer} » importe la bibliothèque "
            f"tierce « {root} » ({module}).\n"
            "Le domaine et les cas d'utilisation n'utilisent que la bibliothèque standard : "
            "c'est ce qui garantit qu'ils restent testables sans base, sans serveur et sans "
            f"appel à un service IA réel. {RULES_REFERENCE}"
        )


@pytest.mark.parametrize(("path", "layer"), MODULES, ids=MODULE_IDS)
def test_les_importations_sont_absolues(path: Path, layer: str) -> None:
    """Les importations relatives masqueraient la couche visée aux tests ci-dessus."""
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.ImportFrom) and node.level:
            pytest.fail(
                f"{_module_id(path)}:{node.lineno} — importation relative "
                f"(« {'.' * node.level}{node.module or ''} »). "
                f"Le projet n'utilise que des importations absolues, à partir de "
                f"« {PACKAGE}. », pour que les frontières restent lisibles et vérifiables."
            )
