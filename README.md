# AgentScope

Exploration normalisée de traces d'agents de développement IA : **importer, vérifier,
normaliser, explorer**.

AgentScope réunit des traces provenant de plusieurs agents (Claude Code, Codex…), aux
formats et aux conventions différents, dans un modèle relationnel commun, puis les rend
lisibles dans un tableau de bord. Une source dont la structure n'est pas encore connue peut
être intégrée **par configuration**, avec l'aide d'un agent IA qui propose un mapping —
que l'utilisateur relit, corrige et valide avant tout import.

> Projet en cours de construction. Ce README sera complété au fil du sprint par le lot 6.

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

```bash
cd backend  && pytest          # domaine, cas d'utilisation, API, architecture
cd frontend && npm run test    # composants
```

Aucun test n'appelle un service IA réel ni ne nécessite une base de données : c'est une
règle du projet, pas une commodité.

## Configuration du modèle IA

Le fournisseur, le modèle et son point d'accès se choisissent dans `backend/.env`, sans
toucher au code. Trois configurations sont documentées dans `backend/.env.example` :

| Configuration | `AI_PROVIDER` | Clé nécessaire |
|---|---|---|
| Anthropic (distant) | `anthropic` | oui |
| Ollama (local) | `ollama` | non |
| Doublure de test | `fake` | non |

La valeur par défaut est `fake`, pour qu'un clone du dépôt démarre et passe ses tests sans
aucune clé API.

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

## Licence

À définir avant la publication de la release.
