# ADR 0002 — Le domaine et les cas d'utilisation n'ont aucune dépendance externe

- **Statut** : accepté
- **Date** : 2026-09-07
- **Décideurs** : le groupe

## Contexte

L'énoncé demande que les règles de normalisation, de validation et de calcul des indicateurs
soient testables sans lancer l'interface ni appeler un service IA réel, et qu'un changement
d'interface ou de fournisseur d'IA n'oblige pas à les réécrire.

Des dossiers nommés `domain` et `infrastructure` ne suffisent pas : sans contrainte
appliquée, une importation de SQLAlchemy finit toujours par se glisser dans une règle
métier, et la séparation devient décorative.

## Décision

Les dépendances vont vers l'intérieur, et l'intérieur ne dépend de rien :

| Couche | Peut importer | Dépendances externes |
|---|---|---|
| `domain/` | rien | aucune |
| `application/` | `domain` | aucune |
| `infrastructure/` | `domain`, `application` | oui |
| `interfaces/` | `domain`, `application` | oui |
| `composition.py` | tout | oui |

`domain/` et `application/` n'utilisent que la bibliothèque standard. Les cas d'utilisation
dialoguent avec des ports — des classes abstraites déclarées dans `application/ports/` — dont
les implémentations concrètes vivent dans `infrastructure/` et sont câblées en un seul
endroit, `composition.py`.

`interfaces/` n'importe pas `infrastructure/` : la construction des objets concrets est le
travail de la racine de composition, pas des routeurs.

**Cette règle est vérifiée par un test** (`tests/architecture/test_layer_dependencies.py`)
qui analyse les importations de chaque module et échoue si une frontière est franchie. Il
tourne dans la CI.

## Conséquences

**Ce que ça apporte.** Les règles métier se testent en millisecondes, sans base, sans
serveur, sans réseau. Changer de fournisseur d'IA ou de moteur de stockage se limite à
écrire un adaptateur et à modifier une ligne de câblage. Et la séparation est réelle, parce
qu'elle est mesurée.

**Ce que ça coûte.** On écrit nos propres entités au lieu de réutiliser directement les
modèles SQLAlchemy ou les schémas Pydantic : il y a une traduction à faire aux frontières,
donc du code de conversion en plus. C'est le prix assumé de l'indépendance du cœur métier.

Ça coûte aussi une discipline : Pydantic est très pratique et la tentation de le faire
descendre dans le domaine est constante. Le test d'architecture est là pour que la
discipline ne repose pas sur la vigilance de six personnes fatiguées un jeudi soir.

## Alternatives écartées

- **Convention sans vérification** — c'est ce qu'on fait quand on veut que la règle soit
  violée avant la fin de la semaine.
- **Pydantic dans le domaine** — pratique, mais introduit une dépendance externe au cœur et
  brouille la frontière entre une entité métier et un schéma de transport.
- **Une bibliothèque d'injection de dépendances** — inutile à cette taille : un constructeur
  et une fonction de câblage suffisent, et se lisent sans documentation.
