# AgentScope

Exploration normalisée de traces d'agents de développement IA : **importer, vérifier,
normaliser, explorer**.

AgentScope réunit des traces provenant de plusieurs agents (Claude Code, Codex…), aux
formats et aux conventions différents, dans un modèle relationnel commun, puis les rend
lisibles dans un tableau de bord. Une source dont la structure n'est pas encore connue peut
être intégrée **par configuration**, avec l'aide d'un agent IA qui propose un mapping —
que l'utilisateur relit, corrige et valide avant tout import.

**Version `v0.1.0`** — voir les [notes de version](CHANGELOG.md) pour les fonctionnalités
livrées et les limites connues.

## Prérequis

| Outil | Version |
|---|---|
| Python | 3.12 |
| Node.js | 22 |
| Docker | pour PostgreSQL |

## Démarrage

```bash
git clone https://github.com/SoufianeBenmouhoub/Projet-AgentScope.git
cd Projet-AgentScope
```

**1. La base de données**

```bash
docker compose up -d
```

**2. Le back**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e ".[dev]"
cp .env.example .env
uvicorn agentscope.main:app --reload
```

L'API écoute sur http://localhost:8000, sa documentation sur http://localhost:8000/docs.

**3. Le front**

```bash
cd frontend
npm install
npm run dev
```

L'interface est sur http://localhost:5173. En développement, Vite redirige `/api` vers le
back : rien d'autre à configurer.

## Tests

Depuis la racine du dépôt, dans deux terminaux ou l'un après l'autre :

```bash
cd backend
pytest                  # domaine, cas d'utilisation, API, architecture
```

```bash
cd frontend
npm run test            # composants et écrans
npm run lint            # vérification des types
```

**Aucun test n'appelle un service IA réel** : c'est une règle du projet, pas une commodité.
L'adaptateur `fake` est là pour ça.

Une poignée de tests vérifient la traduction entre le modèle relationnel et le contrat du
tableau de bord, ce qu'aucune doublure ne peut faire : ils ont besoin d'une base. Sans
PostgreSQL joignable ils sont ignorés, et la suite reste exécutable. Pour les exécuter :

```bash
docker compose up -d
cd backend && alembic upgrade head && pytest
```

## Configuration du modèle IA

Le fournisseur, le modèle et son point d'accès se choisissent dans `backend/.env`, sans
toucher au code. Trois configurations sont documentées dans `backend/.env.example` :

| Configuration | `AI_PROVIDER` | `AI_MODEL` | `AI_BASE_URL` | Clé nécessaire |
|---|---|---|---|---|
| Ollama (local) | `ollama` | le modèle téléchargé | `http://localhost:11434/v1` | non |
| Doublure de test | `fake` | — | — | non |

La valeur par défaut est `fake`, pour qu'un clone du dépôt démarre et passe ses tests sans
aucune clé API.

### Changer de modèle ou de fournisseur

1. Éditer `backend/.env` : `AI_PROVIDER`, `AI_MODEL` et, si le fournisseur l'exige,
   `AI_BASE_URL` et `AI_API_KEY`.
2. Redémarrer le serveur. **Rien d'autre à modifier** — aucun identifiant de modèle n'est
   écrit dans le code, et le moteur d'import ne connaît pas le fournisseur.

Un mapping enregistré avec un modèle reste utilisable après un changement de modèle : il est
stocké sous forme de correspondances entre champs, indépendamment de qui l'a proposé.

Ajouter un fournisseur non pris en charge se limite à écrire un adaptateur dans
`backend/src/agentscope/infrastructure/llm/` et à le raccorder dans
`build_mapping_proposal` (`backend/src/agentscope/composition.py`). Aucune autre partie de
l'application ne change.

Le détail de l'agent et de son contrat est dans [docs/mapping-agent.md](docs/mapping-agent.md).

**Aucune clé API ne doit figurer dans le dépôt.**

## Architecture

Le projet est un monolithe modulaire organisé en couches, dont les dépendances vont
toujours vers l'intérieur :

```
interfaces ──┐
             ├──> application ──> domain
infrastructure ──┘
```

Le cœur métier — `domain/` et `application/` — n'utilise que la bibliothèque standard : il
ne connaît ni FastAPI, ni SQLAlchemy, ni aucun fournisseur d'IA. Cette règle est **vérifiée
par un test** qui tourne dans la CI (`backend/tests/architecture/`).

- **Le schéma des composants et de leurs dépendances : [docs/architecture.md](docs/architecture.md)**
- Les conventions de travail : [CONTRIBUTING.md](CONTRIBUTING.md)
- Les décisions d'architecture : [docs/adr/](docs/adr/)

## Données

- **Provenance, versions et méthode de sélection des extraits :** [docs/data-sources.md](docs/data-sources.md)
- **Trois observations chiffrées tirées des données :** [docs/observations.md](docs/observations.md)
- Le modèle relationnel : [docs/data-model.md](docs/data-model.md)

Aucun jeu de données n'est versionné dans ce dépôt.

## Structure du dépôt

```
backend/
  src/agentscope/
    domain/          règles et entités métier — aucune dépendance
    application/     cas d'utilisation et ports — aucune dépendance
    infrastructure/  PostgreSQL, DuckDB, adaptateurs IA
    interfaces/      API HTTP
    composition.py   racine de composition : le seul endroit qui choisit les implémentations
    main.py          point d'entrée
  alembic/           migrations
  tests/
frontend/
  src/features/      un dossier par domaine fonctionnel
  src/shared/        client HTTP, types d'API
docs/
  adr/               décisions d'architecture
  brief/             énoncé du projet
```

## État du projet

Le parcours principal existe de bout en bout, avec des limites assumées et documentées.
Elles sont listées sans détour dans les [notes de version](CHANGELOG.md) — notamment le fait
que la normalisation ne produit encore que des sessions, et que l'import n'est pas
déclenchable depuis l'interface.

## Contribuer

Les conventions de travail, la règle des couches et ce qu'on regarde dans une revue sont
dans [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

[MIT](LICENSE).
