"""Couche infrastructure — les implémentations concrètes des ports.

C'est ici, et seulement ici, que vivent SQLAlchemy, DuckDB, les SDK des fournisseurs d'IA
et la lecture du système de fichiers. Rien de cette couche ne remonte vers `application/`
ou `domain/`.
"""
