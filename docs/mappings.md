# Mappings

Un mapping associe **un champ du modèle commun** à **un chemin dans l'enregistrement
source**. C'est de la configuration, pas du code : intégrer une source revient à écrire ce
tableau, jamais à modifier le moteur d'import.

## Le contrat

Les champs acceptés sont déclarés dans
[`domain/mapping/contract.py`](../backend/src/agentscope/domain/mapping/contract.py), et
exposés par l'API — l'agent IA les vise, l'utilisateur les corrige, le moteur les applique.

| Champ | Portée | Obligatoire |
|---|---|:-:|
| `session_id` | session | **oui** |
| `agent`, `session_status` | session | |
| `occurred_at`, `ended_at` | appel au modèle | |
| `model`, `model_call_id` | appel au modèle | |
| `input_tokens`, `output_tokens`, `cache_creation_tokens` | appel au modèle | |
| `tools` | **chemin du tableau** des appels d'outils | |
| `tool_name`, `tool_call_id`, `tool_started_at`, `tool_ended_at`, `tool_is_error`, `tool_error` | appel d'outil | |

Seul `session_id` est obligatoire : sans lui, un enregistrement ne peut être rattaché à
rien. Tout le reste peut rester vide — **une mesure non renseignée reste absente, elle ne
devient pas zéro.**

### Syntaxe des chemins

Un point pour descendre, des crochets pour choisir un élément :

```
provider
timing_events[0].timestamp
tools
```

La syntaxe est **déclarative et fermée** : aucun code produit par un modèle n'est exécuté, et
un chemin qui ne mène nulle part rend une absence plutôt qu'une erreur.

---

## Source 1 — TraceLab (JSONL)

Format imbriqué : une ligne est **une invocation du modèle**, avec ses appels d'outils dans
un tableau et ses horodatages dans un autre.

```json
{
  "session_id": "session_id",
  "agent": "provider",
  "occurred_at": "timing_events[0].timestamp",
  "model": "model",
  "model_call_id": "round_id",
  "input_tokens": "input_tokens_total",
  "output_tokens": "output_tokens",
  "cache_creation_tokens": "claude_cache_creation_input_tokens",
  "tools": "tools",
  "tool_name": "tool_name",
  "tool_call_id": "tool_call_id",
  "tool_started_at": "emitted_at",
  "tool_ended_at": "result_at",
  "tool_is_error": "is_error"
}
```

**Résultat vérifié** sur l'extrait de 240 sessions :

```
enregistrements lus : 15 913     sessions : 240
appels au modèle    : 15 913     appels d'outils : 15 969     anomalies : 0
```

Trois points méritent d'être notés :

**240 sessions, pas 15 913.** Plusieurs enregistrements partagent un `session_id` : le
moteur les regroupe et déduit les bornes de la session du plus tôt au plus tard de ses
invocations.

**`cache_creation_tokens` reste vide pour Codex.** Le champ n'existe pas dans ses
enregistrements. C'est le comportement voulu : l'indicateur s'affiche indisponible pour cet
agent au lieu d'afficher zéro.

**La latence des outils n'est pas mappée directement.** TraceLab publie un
`tool_wall_latency_ms`, mais le modèle commun préfère les bornes : `emitted_at` et
`result_at` donnent la durée, et restent exploitables pour une source qui ne calculerait pas
la latence elle-même.

---

## Source 2 — Un format tabulaire plat (CSV)

Le même moteur, sans aucune modification, avec un fichier plat où chaque ligne est déjà une
session. C'est le cas le plus simple, et il montre que le mapping absorbe aussi bien un
format à plat qu'un format imbriqué.

```json
{
  "session_id": "conversation_id",
  "agent": "agent_name",
  "occurred_at": "started_at",
  "ended_at": "finished_at",
  "model": "model_name",
  "input_tokens": "prompt_tokens",
  "output_tokens": "completion_tokens"
}
```

Sans champ `tools`, aucun appel d'outil n'est produit — ce n'est pas une anomalie, seulement
une source qui n'en publie pas. Les indicateurs correspondants s'affichent indisponibles.

---

## Ce qu'un mapping ne peut pas encore faire

- **Aucune transformation de valeur.** Un mapping choisit un champ, il ne le convertit ni ne
  le combine. Une source dont les dates seraient en secondes Unix ne pourrait pas être
  intégrée sans étendre le moteur.
- **Un seul niveau de tableau.** `tools[]` est parcouru, mais pas un tableau à l'intérieur
  d'un tableau.
- **Pas encore enregistré ni réutilisable.** Le mapping se fournit à chaque import ; le
  stocker pour le rejouer sur un fichier suivant reste à faire.
