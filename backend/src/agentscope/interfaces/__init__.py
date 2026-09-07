"""Couche interfaces — l'exposition de l'application vers l'extérieur.

Aujourd'hui une API HTTP ; demain, éventuellement, une ligne de commande. Cette couche
traduit des requêtes en appels de cas d'utilisation et des objets de domaine en réponses.
Elle ne contient aucune règle métier et n'importe jamais `infrastructure/`.
"""
