"""Utilitaires de calcul d'empreinte des fichiers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_file_hash(path: Path) -> str:
    """Retourne le hash SHA-256 du contenu du fichier."""
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()
