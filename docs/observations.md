# Trois observations tirées des données

Toutes portent sur le même extrait : **TraceLab v0.0.2, 240 sessions, 15 913 invocations du
modèle, 15 969 appels d'outils, du 9 novembre 2025 au 3 juin 2026.** Sa méthode de
construction est décrite dans [`data-sources.md`](data-sources.md).

**Les chiffres sont calculés par le programme**, jamais estimés :

```bash
python scripts/observations.py chemin/vers/tracelab-extrait.jsonl
```

> Ce script lit l'extrait brut plutôt que la base. À ce jour, la normalisation ne produit
> que des sessions : les appels d'outils, sur lesquels portent les deux premières
> observations, ne sont pas encore importés. Chaque observation indique l'écran et le filtre
> qui la montreront dès que ce sera le cas.

---

## 1. Un appel d'outil sur vingt échoue, et cent cinq n'ont aucune issue connue

| | |
|---|---|
| Appels d'outils | 15 969 |
| Dont l'issue est connue | 15 864 |
| En erreur | 772 |
| **Taux d'erreur** | **4,87 %** |
| Issue inconnue | 105 |

Le taux est rapporté aux seuls appels dont l'issue est connue. Compter les 105 inconnus
comme des réussites donnerait 4,83 % — un écart faible ici, mais qui va toujours dans le
même sens : **il sous-estime le taux d'échec**, et l'écart croît avec la part d'inconnus.
C'est pourquoi l'indicateur les exclut du dénominateur plutôt que de les assimiler à des
succès.

*Où la retrouver :* tableau de bord, indicateur « Taux d'erreur des appels d'outils », sans
filtre. Le panneau de qualité des données indique en parallèle combien d'appels sont exclus
du calcul.

---

## 2. La moyenne des latences vaut cent quatre fois la médiane

| | |
|---|---|
| Mesures | 15 941 |
| **Médiane** | **117 ms** |
| p90 | 12 755 ms |
| p99 | 162 539 ms |
| Moyenne | 12 171 ms |

Un appel d'outil sur deux répond en moins de **117 millisecondes**. Un sur cent dépasse
**deux minutes et demie**.

C'est la justification empirique d'un choix fait avant d'avoir vu ces données : l'indicateur
de latence est une **médiane**, pas une moyenne. Une moyenne de 12 secondes décrirait un
outillage lent, alors que l'expérience ordinaire est quasi instantanée — elle ne décrirait
ni le cas courant, ni les cas extrêmes, seulement un point qui n'existe nulle part.

*Où la retrouver :* tableau de bord, indicateur « Latence médiane des appels d'outils », et
le détail par outil dans la vue tableau du graphique de répartition.

---

## 3. Un des deux agents ne publie pas du tout la mesure de cache

| Agent | Invocations renseignant la mesure | Tokens de création de cache |
|---|---|---|
| `claude` | 12 545 / 12 545 — **100 %** | 67 616 231 |
| `codex` | 0 / 3 368 — **0 %** | — |

Claude publie systématiquement `claude_cache_creation_input_tokens` ; Codex ne le publie
jamais. Un total unique sur les deux agents afficherait 67,6 millions de tokens en laissant
croire que Codex en consomme zéro, alors que **la mesure n'existe simplement pas pour lui**.

C'est le cas concret qui justifie deux mécanismes du projet : cet indicateur est marqué
comme propre à une source et se signale dès qu'il agrège plusieurs agents, et le panneau de
qualité affiche « non publié » plutôt qu'un zéro.

*Où la retrouver :* graphique « Tokens par source », qui interroge l'API une fois par source
et laisse un trou explicite là où la mesure n'existe pas — avec la phrase qui le dit sous le
graphique. Le panneau de qualité des données donne la même information sous forme de
complétude par source.

---

## Ce que ces trois observations ont en commun

Aucune n'est un total. Chacune porte sur la différence entre **ce que les données disent** et
**ce qu'un chiffre naïf laisserait croire** : un taux d'erreur qui absorbe les inconnus, une
moyenne qui écrase une distribution asymétrique, un total qui additionne ce qui n'est pas
comparable. C'est précisément ce que le tableau de bord est construit pour éviter.
