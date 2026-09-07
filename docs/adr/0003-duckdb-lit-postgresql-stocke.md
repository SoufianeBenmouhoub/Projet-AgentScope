# ADR 0003 — DuckDB lit les fichiers, PostgreSQL est la source de vérité

- **Statut** : accepté
- **Date** : 2026-09-07
- **Décideurs** : le groupe

## Contexte

L'application doit accepter au minimum du JSONL et un format tabulaire (CSV ou Parquet), et
doit pouvoir profiler un fichier inconnu pour que l'agent IA propose un mapping. En face,
elle doit conserver un modèle relationnel normalisé, avec des clés et des relations
explicites, et garantir qu'un réimport ne crée pas de doublons.

Ce sont deux besoins de nature différente : lire vite et sans schéma préalable d'un côté,
stocker durablement avec des contraintes fortes de l'autre.

## Décision

On sépare les deux rôles :

- **DuckDB est le lecteur.** Il lit JSONL, CSV et Parquet en SQL, sans configuration
  préalable, et sert à produire l'échantillon et le profil de champs présentés à l'agent IA.
  Il ne conserve rien.
- **PostgreSQL est la source de vérité.** Le modèle normalisé, les contraintes d'intégrité,
  la provenance des enregistrements et l'historique des imports y vivent.

L'accès aux fichiers passe par un port (`application/ports/`), donc DuckDB reste un détail
d'implémentation remplaçable.

## Conséquences

**Ce que ça apporte.** Une seule dépendance couvre les trois formats d'entrée exigés, au
lieu d'un analyseur par format. Le profilage d'un fichier inconnu devient une requête SQL
sur le fichier lui-même. Et la base relationnelle garde son rôle : faire respecter le modèle.

**Ce que ça coûte.** Deux moteurs SQL dans le projet, donc deux dialectes à connaître et une
frontière à ne pas franchir mentalement. On l'accepte parce que la frontière est nette :
DuckDB ne voit que des fichiers, PostgreSQL ne voit que le modèle normalisé.

À noter : l'énoncé demande de partir du fichier JSONL publié par TraceLab et non de la base
DuckDB fournie par ce projet. Cette décision ne contredit pas cette consigne — on utilise
DuckDB comme outil de lecture, on n'importe pas la base livrée par TraceLab.

## Alternatives écartées

- **Un analyseur par format** (`json`, `csv`, `pyarrow`) — plus de code, plus de cas
  particuliers, et un profilage à réécrire pour chaque format.
- **DuckDB comme stockage principal** — séduisant pour l'analytique, mais son support des
  contraintes relationnelles est plus limité, ce qui affaiblirait la démonstration du modèle
  de données.
- **Pandas** — dépendance lourde dont on n'utiliserait qu'une fraction, et qui pousse à
  faire du calcul métier dans la couche d'infrastructure.
