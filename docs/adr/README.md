# Décisions d'architecture (ADR)

Un ADR consigne une décision structurante : ce qu'on a choisi, pourquoi, et ce qu'on
accepte de perdre en échange. Il s'écrit **au moment de la décision**, pas à la fin du
projet.

Un ADR fait une page. S'il en fait trois, c'est une note de conception, pas un ADR.

## Modèle

```markdown
# ADR NNNN — Titre à l'affirmative

- **Statut** : proposé | accepté | remplacé par [ADR NNNN](...)
- **Date** : AAAA-MM-JJ
- **Décideurs** : prénoms

## Contexte

Le problème, et les contraintes qui le cadrent. Factuel.

## Décision

Ce qu'on fait. À l'affirmative, au présent.

## Conséquences

Ce que ça nous apporte, et surtout **ce que ça nous coûte**. Un ADR sans coût est un ADR
qui n'a pas été réfléchi.

## Alternatives écartées

Ce qu'on a considéré, et la raison du refus. Une ligne chacune.
```

## Index

| N° | Titre | Statut |
|---|---|---|
| [0001](0001-choix-de-la-stack.md) | Choix de la stack technique | accepté |
| [0002](0002-regle-des-couches.md) | Le domaine et les cas d'utilisation n'ont aucune dépendance externe | accepté |
| [0003](0003-duckdb-lit-postgresql-stocke.md) | DuckDB lit les fichiers, PostgreSQL est la source de vérité | accepté |
| [0004](0004-le-port-de-lecture-renvoie-des-enregistrements.md) | Le port de lecture renvoie des enregistrements, pas des agrégats | accepté |
