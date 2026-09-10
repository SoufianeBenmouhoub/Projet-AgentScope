# Jeux de données

## Ce que le dépôt contient, et ce qu'il ne contient pas

**Aucun jeu de données n'est versionné ici.** Ce document donne la référence exacte, la
méthode de récupération et la méthode de sélection des extraits, pour que n'importe qui
reproduise le même extrait à l'identique.

---

## TraceLab — SyFI Lab, University of Washington

| | |
|---|---|
| Source | https://github.com/uw-syfi/TraceLab |
| Version utilisée | **v0.0.2**, publiée le 24 juillet 2026 |
| Fichier | `syfi_coding_trace.jsonl.gz` — 96,3 Mo compressés |
| Date de récupération | 11 septembre 2026 |
| Licence | voir le dépôt d'origine — **le fichier n'est pas redistribué ici** |

Le fichier JSONL publié est utilisé, **pas** la base DuckDB fournie par le projet, comme le
demande l'énoncé.

### Récupération

```bash
curl -L -o syfi_coding_trace.jsonl.gz \
  https://github.com/uw-syfi/TraceLab/releases/download/v0.0.2/syfi_coding_trace.jsonl.gz
```

### Méthode de sélection de l'extrait

Le fichier complet contient plusieurs centaines de milliers d'invocations. L'extrait de
travail retient **toutes les invocations des 120 premières sessions de chaque agent**
rencontrées dans l'ordre de publication du fichier.

Deux choix méritent d'être justifiés :

**On sélectionne par session, pas par ligne.** Une ligne du fichier est une invocation du
modèle, pas une session : prendre « les N premières lignes » couperait des sessions en
deux, et toute mesure par session — durée, nombre d'appels, tokens — serait fausse.

**On impose un quota par agent.** Le fichier est ordonné, et les premières sessions sont
toutes produites par Claude. Sans quota, l'extrait serait mono-agent et ne permettrait pas
d'observer ce que les deux sources mesurent différemment — ce qui est précisément l'un des
objets du projet.

Le script qui construit l'extrait est [`scripts/build_tracelab_extract.py`](../scripts/build_tracelab_extract.py).

```bash
python scripts/build_tracelab_extract.py chemin/vers/syfi_coding_trace.jsonl.gz
```

### Ce que contient l'extrait

| | |
|---|---|
| Sessions | 240 — 120 par agent |
| Invocations du modèle | 15 913 |
| Agents | `claude` (12 545 invocations), `codex` (3 368) |
| Modèles distincts | 10 |
| Appels d'outils | 15 969, répartis sur 28 outils distincts |
| Période couverte | 9 novembre 2025 → 3 juin 2026 |
| Taille | 27 Mo |

### Structure d'un enregistrement

Une ligne = **une invocation du modèle** au sein d'une session, jamais une session entière.
Les champs utiles au modèle commun :

| Champ | Ce qu'il porte |
|---|---|
| `session_id` | la session à laquelle l'invocation appartient |
| `provider` | l'agent : `claude` ou `codex` |
| `model` | le modèle invoqué |
| `input_tokens_total`, `output_tokens` | les compteurs de tokens |
| `claude_cache_creation_input_tokens` | **publié par Claude uniquement** |
| `timing_events[].timestamp` | les horodatages ; il n'y a pas de date au niveau de l'invocation |
| `tools[]` | les appels d'outils, avec `tool_name`, `is_error`, `tool_wall_latency_ms` |

> ### Deux conséquences pour le moteur d'import
>
> **Le format est imbriqué.** Les appels d'outils vivent dans un tableau `tools[]`, et les
> horodatages dans `timing_events[]`. Un mapping qui n'associe que des champs plats à des
> champs plats ne peut pas les extraire.
>
> **Une session couvre plusieurs lignes.** Ses bornes temporelles se déduisent du minimum
> et du maximum des horodatages de toutes ses invocations. Traiter chaque ligne comme une
> session produirait des dizaines de milliers de sessions d'une seule invocation.

---

## Sources envisagées et non intégrées

**SWE-chat** (SALT-NLP) et **Trace Commons** n'ont pas été intégrés dans cette version. Le
moteur lit déjà JSONL, CSV et Parquet ; ce qui manque est le parcours de mapping éditable
qui permettrait de les intégrer par configuration.
