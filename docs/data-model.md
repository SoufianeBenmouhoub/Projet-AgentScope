# Modèle de données AgentScope

## 1. Objectif

Le modèle de données d'AgentScope permet de normaliser les traces provenant
de différentes sources d'agents de développement IA (Claude Code, Codex, etc.)
dans un modèle relationnel commun.

Il doit permettre de :

- conserver la provenance des données ;
- conserver les données originales importées ;
- représenter les sessions ;
- représenter les appels aux modèles IA ;
- représenter les appels aux outils ;
- éviter les doublons lors d'un réimport ;
- calculer les indicateurs du dashboard ;
- distinguer une donnée absente d'une valeur égale à zéro ;
- conserver les relations entre les différents éléments d'une trace.

PostgreSQL constitue la source de vérité des données normalisées.
DuckDB est utilisé uniquement pour lire et profiler les fichiers sources.

---

## 2. Entités principales

Le modèle repose sur six entités principales :

- **Source** : origine d'un jeu de traces ou d'un dataset.
- **Import** : opération d'importation d'un fichier.
- **RawRecord** : enregistrement original provenant du fichier importé.
- **Session** : session d'utilisation d'un agent.
- **ModelCall** : appel à un modèle IA pendant une session.
- **ToolCall** : appel à un outil pendant une session.

La séparation entre `RawRecord` et les entités normalisées permet de
conserver les données originales même lorsqu'un enregistrement ne peut pas
être entièrement normalisé.

---

## 3. Relations entre les entités

```text
Source
  │
  └──< Import
          │
          ├──< RawRecord
          │
          └──< Session
                  │
                  ├──< ModelCall
                  │
                  └──< ToolCall
---

## 4. Définition des tables

### 4.1 Source

Une ligne de la table `source` représente une source de données externe.

Exemples : TraceLab, SWE-chat ou une autre source compatible.

| Colonne | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | Non | Identifiant interne de la source |
| `name` | TEXT | Non | Nom de la source |
| `version` | TEXT | Oui | Version de la source ou du dataset si connue |
---

## 4. Définition des tables

### 4.1 Source

Représente l'origine des données importées.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | Identifiant unique de la source |
| `name` | VARCHAR | NOT NULL | Nom de la source, ex. TraceLab |
| `agent_name` | VARCHAR | NULL | Agent concerné, ex. Claude Code ou Codex |
| `dataset_version` | VARCHAR | NULL | Version du dataset si connue |
| `created_at` | TIMESTAMP | NOT NULL | Date d'enregistrement de la source |

Une source peut avoir plusieurs imports.

---

### 4.2 Import

Représente une opération d'importation d'un fichier.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | Identifiant unique de l'import |
| `source_id` | UUID | FK → Source | Source du fichier |
| `filename` | VARCHAR | NOT NULL | Nom du fichier importé |
| `file_hash` | VARCHAR | NOT NULL, UNIQUE | Empreinte du fichier permettant d'éviter les réimports |
| `format` | VARCHAR | NOT NULL | JSONL, CSV ou Parquet |
| `imported_at` | TIMESTAMP | NOT NULL | Date de l'import |
| `status` | VARCHAR | NOT NULL | Statut de l'import |
| `records_imported` | INTEGER | NOT NULL | Nombre d'enregistrements importés |
| `duplicates_count` | INTEGER | NOT NULL | Nombre de doublons détectés |
| `rejected_count` | INTEGER | NOT NULL | Nombre de rejets |
| `missing_data_count` | INTEGER | NOT NULL | Nombre d'informations manquantes |

Un même fichier ne doit pas être importé deux fois grâce à `file_hash`.

---

### 4.3 RawRecord

Représente un enregistrement original provenant du fichier importé.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | Identifiant unique |
| `import_id` | UUID | FK → Import | Import dont provient l'enregistrement |
| `record_index` | INTEGER | NOT NULL | Position de l'enregistrement dans le fichier |
| `raw_data` | JSONB | NOT NULL | Données originales de l'enregistrement |
| `record_hash` | VARCHAR | NOT NULL | Empreinte permettant d'identifier un doublon |

`RawRecord` conserve les données originales afin de garantir la traçabilité.

---

### 4.4 Session

Représente une session complète d'utilisation d'un agent.

Une ligne de `Session` correspond à une session d'agent identifiable dans
la source importée.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | Identifiant interne de la session |
| `source_id` | UUID | FK → Source | Source de la session |
| `raw_record_id` | UUID | FK → RawRecord, NULL | Enregistrement original à l'origine de la session |
| `external_id` | VARCHAR | NULL | Identifiant de session fourni par la source |
| `started_at` | TIMESTAMP | NULL | Date de début |
| `ended_at` | TIMESTAMP | NULL | Date de fin |
| `agent_name` | VARCHAR | NULL | Nom de l'agent |
| `status` | VARCHAR | NULL | Statut de la session |

Les dates sont nullables car certaines sources peuvent ne pas fournir
l'information.

---

### 4.5 ModelCall

Représente un appel à un modèle IA effectué pendant une session.

Une ligne de `ModelCall` correspond à un appel individuel au modèle.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | Identifiant unique |
| `session_id` | UUID | FK → Session | Session concernée |
| `external_id` | VARCHAR | NULL | Identifiant fourni par la source |
| `model_name` | VARCHAR | NULL | Nom du modèle utilisé |
| `started_at` | TIMESTAMP | NULL | Début de l'appel |
| `ended_at` | TIMESTAMP | NULL | Fin de l'appel |
| `input_tokens` | INTEGER | NULL | Nombre de tokens en entrée |
| `output_tokens` | INTEGER | NULL | Nombre de tokens en sortie |
| `cached_tokens` | INTEGER | NULL | Nombre de tokens provenant du cache |
| `status` | VARCHAR | NULL | Statut de l'appel |

Les colonnes de tokens sont volontairement nullables.

Une information absente n'est donc pas transformée en `0`.

---

### 4.6 ToolCall

Représente un appel à un outil effectué pendant une session.

Une ligne de `ToolCall` correspond à une utilisation individuelle d'un outil.

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | UUID | PK | Identifiant unique |
| `session_id` | UUID | FK → Session | Session concernée |
| `external_id` | VARCHAR | NULL | Identifiant fourni par la source |
| `tool_name` | VARCHAR | NULL | Nom de l'outil utilisé |
| `started_at` | TIMESTAMP | NULL | Début de l'appel |
| `ended_at` | TIMESTAMP | NULL | Fin de l'appel |
| `status` | VARCHAR | NULL | Statut de l'appel |
| `error` | TEXT | NULL | Erreur éventuelle |

Une ligne représente un appel d'outil, et non un type d'outil.

---

## 5. Règles d'intégrité

Le modèle applique les règles suivantes :

1. Chaque `Import` appartient à une `Source`.
2. Chaque `RawRecord` appartient à un `Import`.
3. Chaque `Session` appartient à une `Source`.
4. Chaque `ModelCall` appartient à une `Session`.
5. Chaque `ToolCall` appartient à une `Session`.
6. Les clés étrangères garantissent que les relations entre les entités
   restent valides.
7. Les mesures inconnues restent `NULL` et ne sont jamais remplacées
   automatiquement par `0`.
8. `file_hash` empêche le réimport du même fichier.
9. `record_hash` permet de détecter les doublons d'enregistrements.
10. Les données originales restent accessibles via `RawRecord`.

---

## 6. Traçabilité

Chaque donnée normalisée doit pouvoir être reliée à sa provenance.

Le chemin de traçabilité principal est :

```text
Source
   ↓
Import
   ↓
RawRecord
   ↓
Session
   ↓
ModelCall / ToolCall

## 7. Diagramme relationnel

```text
┌──────────────┐
│    Source    │
├──────────────┤
│ id PK        │
│ name         │
│ agent_name   │
│ version      │
└──────┬───────┘
       │ 1
       │
       │ N
┌──────▼───────┐
│    Import    │
├──────────────┤
│ id PK        │
│ source_id FK │
│ filename     │
│ file_hash    │
│ format       │
│ status       │
└──────┬───────┘
       │ 1
       │
       │ N
┌──────▼──────────┐
│    RawRecord    │
├─────────────────┤
│ id PK           │
│ import_id FK    │
│ record_index    │
│ raw_data        │
│ record_hash     │
└────────┬────────┘
         │
         │ provenance
         │
┌────────▼────────┐
│     Session     │
├─────────────────┤
│ id PK           │
│ source_id FK    │
│ raw_record_id FK│
│ external_id     │
│ started_at      │
│ ended_at        │
│ agent_name      │
│ status          │
└───────┬─────────┘
        │ 1
        ├────────────────┐
        │ N              │ N
┌───────▼────────┐ ┌─────▼──────────┐
│   ModelCall    │ │    ToolCall    │
├────────────────┤ ├────────────────┤
│ id PK          │ │ id PK          │
│ session_id FK  │ │ session_id FK  │
│ external_id    │ │ external_id    │
│ model_name     │ │ tool_name      │
│ started_at     │ │ started_at     │
│ ended_at       │ │ ended_at       │
│ input_tokens   │ │ status         │
│ output_tokens  │ │ error          │
│ cached_tokens  │ │                │
│ status         │ │                │
└────────────────┘ └────────────────┘

## 8. Gestion des doublons

Le système distingue deux niveaux de doublons.

### Doublon de fichier

L'empreinte `file_hash` identifie un fichier importé.

Deux imports possédant le même `file_hash` sont considérés comme le même
fichier et ne doivent pas créer de nouvelles données.

### Doublon d'enregistrement

Chaque `RawRecord` possède un `record_hash`.

Cette empreinte permet d'identifier deux enregistrements ayant le même contenu,
y compris lorsque les enregistrements proviennent de fichiers différents.

La stratégie exacte de déduplication sera appliquée par le moteur d'import et
testée automatiquement.

## 9. Valeurs absentes

Les informations qui ne sont pas présentes dans une source sont représentées
par `NULL`.

Une valeur absente ne signifie pas que la valeur est égale à zéro.

Par exemple :

- `input_tokens = NULL` signifie que la source ne fournit pas cette information ;
- `input_tokens = 0` signifie que la source indique explicitement zéro token.

Cette distinction est importante pour les indicateurs du dashboard.

Les indicateurs doivent donc ignorer ou signaler les valeurs absentes selon
leur définition, plutôt que de les convertir automatiquement en zéro.

## 10. Évolutivité

Le modèle est conçu pour accueillir plusieurs sources de traces sans modifier
les entités principales.

Une nouvelle source est associée à `Source` et ses données sont converties vers
les entités normalisées lors de l'import.

Les différences entre les formats sources sont traitées par le système de
mapping et de normalisation, et non par la création d'un modèle de données
spécifique à chaque agent.

Les futurs indicateurs du dashboard peuvent utiliser les mêmes entités
normalisées sans dépendre du format original des fichiers.
git 