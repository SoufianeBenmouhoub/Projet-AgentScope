# ADR 0001 — Choix de la stack technique

- **Statut** : accepté
- **Date** : 2026-09-07
- **Décideurs** : le groupe

## Contexte

AgentScope doit ingérer des traces d'agents IA en JSONL, CSV et Parquet, les ranger dans un
modèle relationnel normalisé, les exposer dans un dashboard, et faire appel à un modèle IA
interchangeable pour proposer des mappings. Le tout par six personnes en quatre jours, avec
une architecture qui pèse plus dans l'évaluation que le code lui-même.

Trois contraintes cadrent le choix :

1. Parquet doit être lisible sans bricolage.
2. Le modèle de données est relationnel et normalisé — il faut de vraies contraintes.
3. Une personne extérieure doit pouvoir cloner le dépôt et lancer l'application.

## Décision

- **Back** : Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic.
- **Lecture de fichiers** : DuckDB (JSONL, CSV et Parquet avec une seule dépendance).
- **Base** : PostgreSQL 16, lancée par `docker compose`.
- **Front** : React, Vite, TypeScript, ECharts.
- **Tests** : pytest côté back, Vitest côté front.
- **CI** : GitHub Actions, sur chaque pull request.

## Conséquences

**Ce que ça apporte.** L'écosystème données de Python règle la contrainte Parquet sans
effort. Pydantic v2 sert à la fois de validation d'API et de validateur du contrat de
mapping produit par l'IA. PostgreSQL permet d'exprimer et de faire respecter les clés
étrangères, ce qu'une base à typage laxiste ne permettrait pas de démontrer. ECharts expose
la donnée sous-jacente dans ses événements de clic, ce qui rend le drill-down natif.

**Ce que ça coûte.** Deux langages, donc un risque de dérive entre le contrat exposé par le
back et ce que le front consomme. On l'accepte parce qu'on le neutralise : les types
TypeScript sont générés depuis le schéma OpenAPI de FastAPI, et une divergence casse le
build front au lieu de produire un graphe silencieusement faux.

Ça coûte aussi une dépendance d'infrastructure (Docker pour PostgreSQL). On l'accepte parce
que le démarrage tient en une commande et que le README la documente.

## Alternatives écartées

- **Full TypeScript** — bon pour la coordination, mais le support Parquet côté Node est plus
  fragile, et l'équipe est plus à l'aise en Python côté back.
- **SQLite** — supprime Docker, mais son typage laxiste affaiblit la démonstration du modèle
  relationnel. Reste le repli si Docker devient un obstacle.
- **Streamlit ou un notebook** — rapide à afficher, mais rend impossible la séparation entre
  le domaine et l'interface, qui est l'objet principal de l'évaluation.
- **MongoDB** — incompatible avec l'exigence d'un modèle relationnel normalisé.
