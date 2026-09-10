# Notes de version

## v0.1.0 — 11 septembre 2026

Première version publiable d'AgentScope. Le parcours **importer → vérifier → normaliser →
explorer** existe de bout en bout, avec les limites listées plus bas.

### Ce qui est livré

**Architecture**

- Monolithe modulaire en quatre couches, dont les dépendances vont vers l'intérieur.
- **Le sens des dépendances est vérifié par un test** qui analyse les importations de chaque
  module : une pull request qui fait entrer une bibliothèque tierce dans le cœur métier
  échoue en intégration continue.
- Cinq décisions d'architecture documentées dans `docs/adr/`, et un schéma des composants
  dans `docs/architecture.md`.
- Intégration continue sur chaque pull request : lint, formatage, tests back avec une base
  PostgreSQL réelle, types et tests front, build.

**Modèle de données et ingestion**

- Modèle relationnel normalisé : sources, imports, enregistrements bruts, sessions, appels
  aux modèles, appels d'outils. Migrations Alembic.
- Les données d'origine sont conservées, et chaque enregistrement garde sa provenance.
- **Toutes les colonnes de mesure sont nullables et sans valeur par défaut** : une donnée
  absente ne devient jamais un zéro, du schéma SQL jusqu'à l'écran.
- Lecture de fichiers JSONL, CSV et Parquet via DuckDB.
- **Un réimport du même fichier ne crée pas de doublon** — vérifié par un test.
- **Normalisation pilotée par un mapping déclaratif**, capable de descendre dans des
  structures imbriquées (`timing_events[0].timestamp`) et de parcourir un tableau d'appels
  d'outils. Intégrer une source se fait par configuration, sans toucher au moteur.
- **Les enregistrements sont regroupés en sessions** par identifiant, et les bornes d'une
  session se déduisent du plus tôt au plus tard de ses invocations.
- Vérifié sur des données réelles : **15 913 enregistrements TraceLab → 240 sessions,
  15 913 appels au modèle, 15 969 appels d'outils, 0 anomalie.**

**Agent IA**

- Port commun et adaptateurs isolant chaque fournisseur. Le choix du fournisseur, du modèle
  et de son point d'accès se fait par configuration (`AI_PROVIDER`, `AI_MODEL`,
  `AI_BASE_URL`), sans modifier le code métier.
- Aucun identifiant de modèle n'est écrit en dur.
- Un adaptateur factice permet d'exécuter toute la suite de tests sans appel à un service
  réel.

**Tableau de bord**

- Six indicateurs, chacun accompagné dans l'interface de sa définition : calcul, unité,
  périmètre et traitement des valeurs manquantes.
- Trois visualisations : activité dans le temps, répartition des appels d'outils, tokens par
  source. Palette validée pour les deux thèmes et pour les déficiences de perception des
  couleurs ; chaque graphique a son équivalent en tableau.
- Filtres par source, agent, modèle et période — ce dernier disparaît, avec une explication,
  quand aucun enregistrement n'est horodaté.
- Retour d'un graphique vers les sessions concernées, puis vers l'enregistrement d'origine.
- Panneau de qualité des données : complétude par source, indicateurs indisponibles avec
  leur raison, indicateurs partiels, enregistrements exclus des vues temporelles.

**Import depuis l'interface**

- Aperçu d'un fichier avant import : champs détectés et échantillon de lignes, sans rien
  écrire en base.
- Import d'un fichier avec un mapping explicite entre les champs du fichier et ceux du
  modèle commun. **Un mapping qui désigne un champ inconnu est refusé avec une explication
  qui liste les champs acceptés.**
- Historique des imports et bilan de chaque opération.

**Interface**

- Navigation, écrans tableau de bord, import et système.

### Limites connues

Elles sont listées sans détour : un import partiel correctement expliqué vaut mieux qu'un
import qui paraît réussi et produit des chiffres faux.

- **Un mapping ne transforme pas les valeurs.** Il choisit un champ, il ne le convertit ni ne
  le combine : une source dont les dates seraient en secondes Unix ne pourrait pas être
  intégrée sans étendre le moteur.
- **Un seul niveau de tableau est parcouru.** Les appels d'outils sont lus dans `tools[]`,
  mais pas un tableau imbriqué dans un tableau.
- **Le mapping proposé par l'agent n'est ni enregistré, ni modifiable dans l'interface.**
  L'agent sait analyser un fichier et proposer des correspondances, et l'import accepte un
  mapping explicite — mais le parcours qui relie les deux, avec correction et réutilisation
  d'un mapping enregistré, reste à construire.
- **Le détail des rejets n'est pas conservé.** Le nombre d'anomalies rencontrées pendant la
  normalisation est compté et affiché, mais la liste ligne par ligne de ce qui a été refusé
  n'est pas persistée : la section correspondante de l'interface reste vide.
- **Une seule configuration IA réelle est câblée** (Ollama), à côté de l'adaptateur factice.
  Le second fournisseur reste à raccorder.
- **Le taux d'erreur des appels d'outils est indisponible** : le modèle de données ne
  distingue pas encore « réussi » de « issue inconnue ». Le compter comme un succès
  fausserait le taux, l'indicateur est donc affiché comme indisponible.
- **Les noms d'outils ne sont pas normalisés entre agents.** Un même outil nommé
  différemment par Claude Code et Codex apparaît deux fois dans la répartition.
- **Aucun format tabulaire n'a été démontré de bout en bout.** DuckDB lit CSV et Parquet,
  mais seul JSONL a été importé réellement.
