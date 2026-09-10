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
- Quatre décisions d'architecture documentées dans `docs/adr/`, et trois schémas des
  composants dans `docs/architecture.md`.
- Intégration continue sur chaque pull request : lint, formatage, tests back avec une base
  PostgreSQL réelle, types et tests front, build.

**Modèle de données et ingestion**

- Modèle relationnel normalisé : sources, imports, enregistrements bruts, sessions, appels
  aux modèles, appels d'outils. Migrations Alembic.
- Les données d'origine sont conservées, et chaque enregistrement garde sa provenance.
- **Toutes les colonnes de mesure sont nullables et sans valeur par défaut** : une donnée
  absente ne devient jamais un zéro, du schéma SQL jusqu'à l'écran.
- Lecture de fichiers JSONL, CSV et Parquet via DuckDB. **Un CSV est lu sans types** : un
  fichier plat n'en publie pas, et ceux que le lecteur devinerait effaceraient les zéros
  initiaux d'un identifiant et rendraient illisible une colonne d'horodatages marqués UTC.
- **Un horodatage sans fuseau est rattaché à UTC explicitement**, dans le normaliseur.
  Laissé nu, c'est PostgreSQL qui trancherait selon le fuseau de sa session : le même
  fichier importé sur deux machines donnerait deux instants différents, sans rien signaler.
- **Deux formats vérifiés de bout en bout** : le JSONL imbriqué de TraceLab, et un CSV plat
  où chaque ligne est déjà une session — le même moteur, sans une ligne de code en plus.
- **Un réimport du même fichier ne crée pas de doublon** — vérifié par un test.
- **Normalisation pilotée par un mapping déclaratif**, capable de descendre dans des
  structures imbriquées (`timing_events[0].timestamp`) et de parcourir un tableau d'appels
  d'outils. Intégrer une source se fait par configuration, sans toucher au moteur.
- **Les enregistrements sont regroupés en sessions** par identifiant, et les bornes d'une
  session se déduisent du plus tôt au plus tard de ses invocations.
- Vérifié sur des données réelles : **15 913 enregistrements TraceLab → 240 sessions,
  15 913 appels au modèle, 15 969 appels d'outils, 0 anomalie.**
- **L'issue d'un appel d'outil est à trois états** : réussi, échoué, ou inconnu quand la
  source ne la publie pas. Les inconnus sortent du dénominateur du taux d'erreur au lieu
  d'être comptés comme des réussites.

**Agent IA**

- Port commun et adaptateurs isolant chaque fournisseur. Le choix du fournisseur, du modèle
  et de son point d'accès se fait par configuration (`AI_PROVIDER`, `AI_MODEL`,
  `AI_BASE_URL`), sans modifier le code métier.
- **Deux fournisseurs réels câblés** : un modèle local (Ollama) et un modèle distant
  (Anthropic). Les deux posent la même question et relisent la réponse de la même façon,
  ce qui rend leur comparaison honnête : l'écart vient du modèle, pas de la formulation.
- **Les champs visés par l'IA sont lus dans le contrat du domaine**, pas recopiés dans
  l'adaptateur. Une proposition qui vise un champ hors contrat est écartée et signalée.
- Aucun identifiant de modèle n'est écrit en dur. Un fournisseur réel configuré sans
  `AI_MODEL` est refusé au démarrage, avec la variable à renseigner.
- **Un fournisseur injoignable répond 502, pas une proposition vide** : « le service n'a
  pas répondu » et « aucun champ ne correspond » ne doivent pas se ressembler.
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

- **Le parcours complet tient dans l'écran d'import, sans écrire une ligne de code :**
  aperçu du fichier → proposition de l'agent IA → correction champ par champ → essai à
  blanc → enregistrement du mapping → import avec ce mapping.
- **L'essai à blanc fait tourner le vrai normaliseur** sur l'échantillon, sans rien écrire.
  Il montre les valeurs réellement lues champ par champ, et ce que l'import produirait :
  sessions, appels, anomalies, refus. Sans lui, la seule façon de vérifier un mapping était
  de lancer l'import et de nettoyer la base ensuite.
- **Les champs visés viennent du contrat du domaine**, exposé par l'API. Ni l'interface ni
  l'agent IA n'en gardent une copie qui pourrait diverger.
- **Un mapping vérifié s'enregistre sous un nom et se recharge** sur le fichier suivant. Ce
  qui est conservé, ce sont des correspondances entre champs, pas la proposition d'un
  modèle : un mapping enregistré reste utilisable après un changement de fournisseur IA.
- Aperçu d'un fichier avant import : champs détectés et échantillon de lignes, sans rien
  écrire en base.
- Import d'un fichier avec un mapping explicite entre les champs du fichier et ceux du
  modèle commun. **Un mapping qui désigne un champ inconnu est refusé avec une explication
  qui liste les champs acceptés**, et il l'est aussi bien à l'enregistrement qu'à l'import.
- Historique des imports et bilan de chaque opération.
- **Le détail des rejets est conservé, pas seulement compté.** Un enregistrement que le
  moteur n'a pas pu retenir garde son rang dans le fichier, la raison du refus et le début
  de la ligne d'origine. Un rejet n'est pas compté comme importé, et il se distingue d'une
  information manquante : un compteur illisible ampute un enregistrement, un rejet
  l'écarte entièrement.
- Les rejets du dernier import s'affichent dans le panneau de qualité du tableau de bord :
  ce qui n'est pas entré en base y devient visible, au lieu de laisser des chiffres justes
  porter sur un fichier amputé sans le dire.

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
- **L'essai à blanc porte sur l'échantillon, pas sur le fichier entier.** Un chemin qui
  fonctionne sur les cent premières lignes peut échouer plus loin ; c'est ce que le détail
  des rejets rattrape après coup.
- **Les noms d'outils ne sont pas normalisés entre agents.** Un même outil nommé
  différemment par Claude Code et Codex apparaît deux fois dans la répartition.
- **Parquet n'a pas été importé réellement.** DuckDB le lit et un test le vérifie, mais
  aucun fichier Parquet n'a fait le trajet complet jusqu'au tableau de bord. JSONL et CSV,
  si.
