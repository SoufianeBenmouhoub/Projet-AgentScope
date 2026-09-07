# ADR 0004 — Le port de lecture renvoie des enregistrements, pas des agrégats

- **Statut** : accepté
- **Date** : 2026-09-07
- **Décideurs** : lot 1 et lot 5

## Contexte

Le dashboard doit afficher des indicateurs calculés sur les traces normalisées. Deux
endroits peuvent porter ce calcul :

1. **la base**, via des vues agrégées : rapide, mais la définition d'un indicateur vit
   alors dans du SQL qu'on ne peut pas exécuter sans une base ;
2. **le domaine**, sur des enregistrements lus puis agrégés en mémoire : plus lent sur de
   gros volumes, mais la définition devient du code ordinaire.

L'énoncé tranche en partie : « les règles de normalisation, de validation et de calcul des
indicateurs doivent être testables sans lancer l'interface ni appeler un service IA réel »,
et « une modification de l'interface ou un changement de fournisseur IA ne doit pas imposer
de réécrire ces règles ».

S'ajoute une contrainte propre à ce projet : ce qui distingue une donnée absente d'un zéro,
et ce qui rend une métrique comparable ou non entre deux sources, sont des **règles**, pas
des détails de requête. Les exprimer en SQL les disperserait dans l'infrastructure.

## Décision

`TraceReadPort` expose des enregistrements filtrés — sessions, appels au modèle, appels
d'outils — et non des totaux. L'agrégation, le traitement des valeurs absentes et les
règles de comparabilité vivent dans `domain/metrics/`.

Le port travaille sur des projections étroites : chaque enregistrement ne porte que les
champs dont les indicateurs ont besoin, pas l'intégralité de la ligne. L'implémentation
reste donc libre de ne sélectionner que les colonnes utiles.

## Conséquences

**Ce que ça apporte.** Les définitions d'indicateurs sont testables en millisecondes, sans
base, sans serveur — ce qui est explicitement demandé et noté. Elles sont lisibles par
quelqu'un qui ne connaît pas le schéma SQL. Et la règle « une donnée absente n'est pas un
zéro » est appliquée à un seul endroit, au lieu d'être répétée dans chaque vue.

**Ce que ça coûte.** Les enregistrements du périmètre filtré transitent en mémoire. Sur les
extraits de taille raisonnable que le projet manipule, c'est sans conséquence ; sur un
dataset complet, ça ne tiendrait pas.

Le jour où le volume l'imposera, l'agrégation pourra descendre derrière ce même port — la
signature changera, pas les écrans. Mais on perdra la testabilité qui justifie ce choix
aujourd'hui : ce sera une décision à prendre explicitement et à documenter, pas un
glissement silencieux au détour d'une optimisation.

**Une contrainte que ça impose au modèle de données.** Toutes les colonnes de mesure sont
nullables et sans `DEFAULT 0`. Si l'absence est écrasée en base, aucune règle en aval ne
peut la retrouver, et le domaine calculerait consciencieusement des chiffres faux.

## Alternatives écartées

- **Vues SQL agrégées comme source des indicateurs** — les plus rapides, mais la définition
  d'un indicateur devient intestable sans base, ce que l'énoncé refuse.
- **Un port hybride, agrégats pour les cas lourds et enregistrements pour les autres** —
  deux façons de définir un indicateur dans le même projet, donc deux endroits où la règle
  des valeurs absentes peut diverger. À reconsidérer seulement si la performance devient un
  problème mesuré, pas supposé.
