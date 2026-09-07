"""Tables SQLAlchemy.

Ce module est le point d'entrée du **lot 2** (modèle de données et ingestion) : c'est ici
que sont déclarées les tables du modèle normalisé, et c'est `Base.metadata` qu'Alembic
compare pour générer les migrations.

Deux règles qui viennent de l'énoncé et qui contraignent ce module :

- une mesure absente reste absente. Pas de `default=0` sur une colonne numérique, sinon
  plus rien ne distingue « zéro token » de « cette source ne fournit pas l'information » ;
- la provenance de chaque enregistrement est conservée, et un réimport du même fichier ne
  doit pas produire de doublon — ce qui suppose une contrainte d'unicité, pas seulement un
  filtre applicatif.

Aucun de ces types ne doit traverser la frontière vers `application/` ou `domain/`.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base déclarative commune à toutes les tables du modèle."""
