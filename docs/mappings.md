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

**Résultat vérifié** sur un extrait de quatre lignes, dont deux partagent une conversation
et deux ont une cellule vide :

```
enregistrements lus : 4     sessions : 3
appels au modèle    : 4     appels d'outils : 0     anomalies : 0

sessions_total        3        couverture 3/3
model_calls_total     4        couverture 4/4
input_tokens_total    9 170    couverture 3/4
cache_creation_tokens indisponible, couverture 0/4
```

Trois points, encore :

**Une cellule vide reste vide.** `input_tokens_total` porte sur 3 des 4 appels, et le dit.
La quatrième ligne ne contribue pas zéro à la somme.

**Sans champ `tools`, aucun appel d'outil n'est produit** — ce n'est pas une anomalie,
seulement une source qui n'en publie pas. Les indicateurs correspondants s'affichent
indisponibles, pas à zéro.

**Un CSV est lu sans types.** Un fichier plat n'en publie pas ; ceux que le lecteur
devinerait effaceraient les zéros initiaux d'un identifiant, et rendraient illisible une
colonne d'horodatages uniformément marqués `Z`. Le normaliseur relit chaque valeur selon le
champ qu'elle alimente, ce qui laisse la décision à l'endroit qui sait de quel champ il
s'agit.

---

## Mettre un mapping au point depuis l'interface

Aucune de ces étapes ne demande d'écrire du code. L'écran d'import les enchaîne dans cet
ordre, et chacune répond à une question que la précédente laisse ouverte.

| Étape | Ce qu'on fait | La route |
|---|---|---|
| 1. Aperçu | Lire les champs du fichier et quelques lignes, sans rien écrire | `POST /api/v1/imports/preview` |
| 2. Proposition | Demander à l'agent IA une correspondance | `POST /api/v1/mapping/propose` |
| 3. Correction | Corriger case par case ; les champs visés viennent du contrat | `GET /api/v1/mapping/fields` |
| 4. Essai à blanc | Voir les valeurs réellement lues et ce que l'import produirait | `POST /api/v1/mapping/preview` |
| 5. Enregistrement | Conserver le mapping sous un nom, pour le rejouer | `POST /api/v1/mappings` |
| 6. Import | Importer avec **ce** mapping | `POST /api/v1/imports` |

**L'étape 4 est celle qui manquait.** Sans elle, la seule façon de savoir si un mapping est
juste était de lancer l'import et de regarder la base — puis de la nettoyer quand il ne
l'était pas. L'essai à blanc fait tourner **le vrai normaliseur**, celui de l'import, sur
l'échantillon : ce qu'il annonce est ce que l'import fera.

Il répond à deux questions que rien d'autre ne recoupe :

- **Chaque champ vise-t-il la bonne colonne ?** Les valeurs lues sont affichées. Un chemin
  qui pointe à côté rend une colonne vide (« 0/N ») ; un chemin qui pointe sur la mauvaise
  colonne rend des valeurs qui ne ressemblent pas à ce qu'on attend. Aucun compteur ne
  montre la seconde erreur.
- **Qu'est-ce que ça donnerait ?** Sessions, appels au modèle, appels d'outils, anomalies,
  et le nombre d'enregistrements qui seraient refusés.

**Ce qui est enregistré, ce sont des correspondances entre champs, pas la proposition d'un
modèle.** Un mapping conservé reste donc utilisable après un changement de fournisseur ou
de modèle IA : rien de ce qu'on stocke ne dépend de qui l'a proposé. Réenregistrer sous le
même nom remplace — corriger un mapping consiste à le réenregistrer, et laisser s'accumuler
« tracelab », « tracelab 2 », « tracelab final » ne rendrait service à personne.

Un mapping est validé **avant** d'être conservé. Un mapping inapplicable enregistré
aujourd'hui deviendrait une panne inexplicable le jour où quelqu'un le rechargerait, sur un
autre fichier, sans se souvenir de rien.

---

## Ce qu'un mapping ne peut pas encore faire

- **Aucune transformation de valeur.** Un mapping choisit un champ, il ne le convertit ni ne
  le combine. Une source dont les dates seraient en secondes Unix ne pourrait pas être
  intégrée sans étendre le moteur.
- **Un seul niveau de tableau.** `tools[]` est parcouru, mais pas un tableau à l'intérieur
  d'un tableau.
- **L'essai à blanc porte sur l'échantillon, pas sur le fichier entier.** Un chemin qui
  fonctionne sur les cent premières lignes peut échouer plus loin. C'est pourquoi l'import
  conserve aussi le détail de ses rejets.
