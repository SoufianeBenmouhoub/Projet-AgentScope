"""Schémas d'entrée et de sortie de l'API.

Ce sont des objets de **transport**, distincts des entités de domaine. Ils peuvent changer
pour des raisons d'interface (nommage, format, compatibilité) sans que le domaine bouge —
et c'est précisément l'intérêt de les séparer.

Ces schémas alimentent le document OpenAPI, à partir duquel le front génère ses types
TypeScript : une divergence entre le back et le front casse le build au lieu de produire
un affichage silencieusement faux.
"""
