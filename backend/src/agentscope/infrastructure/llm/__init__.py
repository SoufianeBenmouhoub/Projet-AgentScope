"""Adaptateurs des fournisseurs d'IA.

Point d'entrée du **lot 4**. Un adaptateur par fournisseur, tous derrière le même port
déclaré dans `application/ports/`, tous sélectionnés par configuration (`AI_PROVIDER`).

Ajouter un fournisseur non encore pris en charge doit se limiter à déposer un module ici et
à le raccorder dans `composition.py`. Aucune autre partie de l'application ne change.

Trois adaptateurs sont prévus : `anthropic`, `ollama` et `fake` — ce dernier étant celui
qu'utilisent les tests automatisés, qui n'appellent jamais un service réel.
"""
