# Compte rendu de vérification — parcours d'identification et d'import

**Auteur :** Narimen Boumaout
**Date :** 11 septembre 2026
**Périmètre :** vérification en conditions réelles du parcours complet (import → proposition
de mapping par l'IA → correction → aperçu → enregistrement → import) avec les deux
fournisseurs IA gratuits configurés pour ce projet : Ollama (local) et Groq (distant).

Aucune clé API ni donnée sensible n'apparaît dans ce document. Le fichier de test utilisé
(`tracelab_sample.jsonl`) est entièrement synthétique, fabriqué pour cette vérification.

## Configuration testée

| Fournisseur | Modèle | Type |
|---|---|---|
| Ollama | `mistral` | local, gratuit |
| Groq | `openai/gpt-oss-120b` | distant, gratuit |

## Méthode

1. Démarrage complet de la stack (PostgreSQL via Docker, backend FastAPI, frontend Vite).
2. Import d'un fichier JSONL synthétique au format TraceLab (3 sessions, 4 appels au
   modèle, 4 appels d'outils, dont un en erreur).
3. Pour chaque fournisseur : proposition de mapping par l'agent IA, relecture des
   champs proposés, correction des erreurs constatées, vérification sur l'échantillon
   (aperçu sans écriture), puis import réel et contrôle du tableau de bord.

## Résultats

### Ollama (mistral)

- Le modèle répond correctement mais lentement (30 secondes à 2 minutes selon l'état de
  chargement en mémoire).
- À plusieurs reprises, le modèle a renvoyé un JSON mal formé. Le système l'a détecté et
  affiché clairement (« Réponse IA non exploitable : ... ») sans planter ni deviner —
  comportement attendu et vérifié.
- Un nouvel essai suffit généralement à obtenir une réponse exploitable.
- Le mapping proposé était globalement correct (`session_id`, `model`, tokens), avec
  quelques champs à corriger manuellement (chemins de type `tools[...]` invalides,
  index négatifs non supportés) — corrigés sans difficulté via l'interface.

### Groq (openai/gpt-oss-120b)

- Réponse rapide et fiable (quelques secondes).
- Mapping proposé de bonne qualité, avec des notes explicites pour les champs non
  résolus.
- **Bug détecté et corrigé pendant cette vérification** : le modèle renvoyait parfois la
  chaîne de texte `"NULL"` au lieu de la valeur JSON `null` pour un champ absent, ce qui
  contournait silencieusement la détection de correspondance non résolue. Corrigé dans
  `infrastructure/llm/prompt.py` (fonction `_normalized_source_field`), avec un test de
  non-régression ajouté. Correctif déployé et vérifié en conditions réelles après
  correction.

### Comportement commun vérifié

- Les deux fournisseurs respectent le principe de conception du projet : un champ non
  identifiable est explicitement laissé vide, jamais deviné.
- Un chemin de champ invalide (syntaxe non supportée, index négatif) est rejeté
  clairement par le système plutôt que silencieusement ignoré.
- Le parcours complet (import → mapping → aperçu → import réel → tableau de bord)
  fonctionne de bout en bout avec les deux fournisseurs.

## Bug trouvé sur `main` (indépendant des fournisseurs IA)

En testant l'aperçu de mapping (`POST /api/v1/mapping/preview`) directement, indépendamment
de tout appel IA, un bug a été identifié dans
`backend/src/agentscope/application/use_cases/preview_mapping.py` (fonction `_outcome`) :
les champs de portée « appel d'outil » (`tool_name`, `tool_started_at`, `tool_ended_at`,
`tool_is_error`, `tool_call_id`) sont résolus directement sur l'enregistrement complet, au
lieu d'être lus à l'intérieur de chaque élément du tableau `tools`. Résultat : ces champs
affichent systématiquement « 0 résolu » dans l'aperçu, même avec un mapping correct.

Le véritable import (via `RecordNormalizer.normalize`, utilisé plus haut dans la même
fonction) semble correctement gérer cette portée — le nombre d'appels d'outils créés était
juste (4/4) lors des tests. Il s'agit donc probablement d'un bug d'affichage dans l'aperçu,
pas dans l'import réel, mais il peut induire en erreur un utilisateur qui vérifie son
mapping avant d'importer. Signalé à l'équipe le 11 septembre 2026.

## Conclusion

Le parcours d'identification et d'import fonctionne de bout en bout avec les deux
fournisseurs IA gratuits (Ollama, Groq). Un bug de traitement de réponse (Groq) et un bug
d'affichage de l'aperçu (indépendant des fournisseurs) ont été trouvés au cours de cette
vérification ; le premier est corrigé, le second est documenté et signalé à l'équipe.