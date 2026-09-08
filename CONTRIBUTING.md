# Contribuer à AgentScope

Ce document est la référence de travail de l'équipe. Il tient en une page volontairement :
tout ce qui n'y est pas est laissé au jugement de la personne qui code.

## 1. Le découpage en lots

Chaque personne est responsable d'un lot. On ne modifie pas le code d'un autre lot sans
prévenir la personne concernée — on ouvre une issue ou on lui demande.

| Lot | Périmètre | Où ça vit |
|---|---|---|
| 1 — Architecture | Structure, conventions, CI, ADR, revue des PR structurantes | Racine, `.github/`, `docs/`, `composition.py` |
| 2 — Modèle & ingestion | Modèle relationnel, migrations, normalisation, dédoublonnage, moteur d'import | `domain/trace/`, `infrastructure/persistence/`, `alembic/` |
| 3 — Connecteur TraceLab | Mapping TraceLab, bilan d'import, provenance des données | `infrastructure/sources/` |
| 4 — Agent IA | Profilage, proposition de mapping, port IA et ses adaptateurs | `domain/mapping/`, `infrastructure/llm/` |
| 5 — Dashboard | Indicateurs, visualisations, vue session, filtres, drill-down, qualité | `domain/metrics/`, `frontend/src/features/dashboard/` |
| 6 — UI & publication | Coquille de l'application, écrans d'import et de mapping, doc, release | `frontend/src/app/`, `frontend/src/features/import/`, `README.md` |

### Les dossiers partagés

`application/ports/`, `application/use_cases/` et `interfaces/api/` sont **communs à tous
les lots**. On n'y crée pas de sous-dossier par lot : un fichier par concept, dont le nom
porte le sujet.

| Vous écrivez | Ça va dans | Nommage |
|---|---|---|
| une interface attendue de l'extérieur | `application/ports/` | le sujet : `trace_read.py`, `mapping_proposer.py` |
| un cas d'utilisation | `application/use_cases/` | un verbe : `propose_mapping.py`, `get_kpi_summary.py` |
| une route HTTP | `interfaces/api/routers/` | la ressource : `metrics.py`, `sessions.py` |
| un schéma d'entrée/sortie | `interfaces/api/schemas/` | idem |
| une entité ou une règle métier | `domain/<votre sujet>/` | groupé par sujet |
| une implémentation concrète | `infrastructure/<votre sujet>/` | groupé par sujet |

Pourquoi le domaine est groupé par sujet et pas la couche application : le domaine contient
beaucoup de petits fichiers par concept, la couche application n'en contient qu'un ou deux.
Un dossier par lot dans `application/` ajouterait un niveau pour ranger deux fichiers.

Quand vous ajoutez un cas d'utilisation destiné à être appelé de l'extérieur, déclarez-le
dans `application/container.py` et câblez-le dans `composition.py`.

## 2. La règle des couches

C'est la règle la plus importante du projet. **Les dépendances vont toujours vers l'intérieur.**

```
interfaces ──┐
             ├──> application ──> domain
infrastructure ──┘
```

| Couche | Peut importer | Dépendances externes autorisées |
|---|---|---|
| `domain/` | rien | **aucune** — bibliothèque standard uniquement |
| `application/` | `domain` | **aucune** — bibliothèque standard uniquement |
| `infrastructure/` | `domain`, `application` | oui (SQLAlchemy, DuckDB, SDK IA…) |
| `interfaces/` | `domain`, `application` | oui (FastAPI, Pydantic) |
| `composition.py` | tout | oui |

Concrètement :

- Le domaine et les cas d'utilisation ne connaissent ni FastAPI, ni SQLAlchemy, ni aucun
  fournisseur d'IA. Ils parlent à des **ports** (classes abstraites de `application/ports/`).
- Les implémentations concrètes vivent dans `infrastructure/` et sont câblées dans
  `composition.py`, à un seul endroit.
- `Depends` de FastAPI n'apparaît que dans `interfaces/`.
- Les types générés par une bibliothèque (modèles SQLAlchemy, schémas Pydantic d'API) ne
  traversent jamais la frontière vers `application/` ou `domain/`.

Cette règle n'est pas déclarative : elle est **vérifiée automatiquement** par
`backend/tests/architecture/test_layer_dependencies.py`, qui tourne dans la CI. Une PR qui
la viole est rouge.

## 3. Branches

**Une branche par sujet**, partant de `main` à jour :

```
<type>/<description-courte>
```

Exemples réels : `feature/thanu-design-data-model`, `mel/tracelab-import`,
`feature/agent-ia-setup`.

Types : `feature`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`.

Chaque branche revient sur `main` par pull request. Personne ne pousse sur la branche d'un
autre.

**Ouvre une pull request dès qu'un morceau cohérent est terminé**, sans attendre d'avoir
fini tout ton lot : une PR de 800 lignes n'est pas relue, elle est approuvée.

**Reste synchronisé avec `main` au moins une fois par jour**, sinon l'intégration de fin de
semaine devient un chantier :

```bash
git fetch origin
git merge origin/main
```

## 4. Commits

Format [Conventional Commits](https://www.conventionalcommits.org/) :

```
<type>(<portée>): <description à l'impératif, en minuscule>
```

Types : `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`.

Exemples :

```
feat(metrics): ajoute l'indicateur de consommation de tokens
fix(ingestion): ignore les lignes déjà importées lors d'un réimport
docs(adr): consigne le choix DuckDB pour la lecture des fichiers
```

Un commit ne mélange pas deux intentions. On n'a pas besoin de beaucoup de commits — on a
besoin de commits lisibles.

## 5. Pull requests

- **Aucun commit direct sur `main`.** La branche est protégée.
- Une PR est reliée à une issue (`Closes #12`) et reste dans le périmètre d'un lot.
- **Une revue par une autre personne du groupe est obligatoire** avant intégration.
- La CI doit être verte.

Chaque membre doit relire des PR, pas seulement en ouvrir. C'est un critère d'évaluation.

### Ce qu'on regarde dans une revue

Approuver sans lire ne fait pas avancer le projet : ça déplace simplement le problème vers
la personne qui découvrira l'erreur trois jours plus tard. Cinq points, dans cet ordre :

1. **Le sens des dépendances.** Une importation qui remonte vers l'extérieur, un type de
   bibliothèque qui entre dans `domain/` ou `application/`. Le test d'architecture attrape
   la plupart des cas, pas tous.
2. **Les interfaces partagées.** Un port, un schéma d'API ou une colonne de mesure qui
   change concerne quelqu'un d'autre. Vérifie que la section « impact sur les autres lots »
   de la PR est remplie, et que la personne concernée est au courant.
3. **Les tests.** Une règle métier sans test n'est pas terminée. Un test qui a besoin d'une
   base ou d'un appel réseau est un test à refaire.
4. **Le traitement des valeurs absentes.** C'est l'erreur la plus coûteuse du projet et la
   plus discrète : un `DEFAULT 0`, un `or 0`, un `?? 0` transforme silencieusement « on ne
   sait pas » en « zéro », et le dashboard affiche des chiffres faux avec assurance.
5. **Ce que la documentation promet.** Si la PR ajoute un document livrable, ouvre-le et
   regarde son rendu.

Ce qu'on ne regarde **pas** : le style et le formatage. `ruff` et `tsc` s'en chargent.

Une revue utile laisse au moins un commentaire ou une question. Si tu n'as vraiment rien à
dire, écris-le — au moins on saura que tu as lu.

## 6. Tests

| Quoi | Où | Doit tourner sans |
|---|---|---|
| Règles de domaine | `backend/tests/domain/` | base, serveur, réseau |
| Cas d'utilisation | `backend/tests/application/` | base, serveur, IA réelle (on utilise les doublures de `tests/fakes/`) |
| Adaptateurs | `backend/tests/infrastructure/` | IA réelle |
| API | `backend/tests/interfaces/` | base réelle |
| Architecture | `backend/tests/architecture/` | tout |
| Front | `frontend/src/**/*.test.tsx` | back réel |

Règle non négociable : **aucun test n'appelle un service IA réel.** L'adaptateur `fake` est
là pour ça (`AI_PROVIDER=fake`).

## 7. Secrets et données

- Aucune clé API dans le dépôt, dans le code livré au navigateur, ni dans un test.
  Tout passe par `.env`, dont seul `.env.example` est commité.
- Aucun jeu de données commité tant que ses conditions de redistribution n'ont pas été
  vérifiées. On documente la provenance et la méthode de récupération dans `docs/data/`.
- Les textes contenus dans les traces sont des **données à analyser**, jamais des
  instructions à exécuter — ni par l'application, ni par le modèle IA.

## 8. Décisions d'architecture

Toute décision structurante donne lieu à un ADR court dans `docs/adr/`, écrit **au moment
de la décision**. Voir `docs/adr/README.md` pour le modèle.
