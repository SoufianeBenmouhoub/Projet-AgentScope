"""Lecteur de fichiers basé sur DuckDB."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from agentscope.application.ports.file_read import FileReadPort


class DuckDBFileReader(FileReadPort):
    """Implémentation de FileReadPort avec DuckDB."""

    def read(
        self,
        path: Path,
        file_format: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lit un fichier et retourne tous ses enregistrements."""
        query = self._build_query(path, file_format)
        return self._execute(query)

    def sample(
        self,
        path: Path,
        file_format: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retourne un échantillon des enregistrements."""
        if limit <= 0:
            return []

        query = self._build_query(path, file_format)
        query = f"{query} LIMIT {limit}"
        return self._execute(query)

    def _build_query(
        self,
        path: Path,
        file_format: str | None,
    ) -> str:
        """Construit la requête DuckDB adaptée au format du fichier."""
        resolved_format = self._resolve_format(path, file_format)
        escaped_path = str(path).replace("'", "''")

        if resolved_format == "jsonl":
            return f"SELECT * FROM read_json_auto('{escaped_path}')"

        if resolved_format == "csv":
            # Toutes les colonnes en texte, délibérément. Un CSV n'a pas de types : ceux que
            # DuckDB devine sont une interprétation, et elle coûte deux fois. Une colonne
            # d'horodatages uniformément marqués « Z » devient un TIMESTAMP WITH TIME ZONE
            # dont la conversion vers Python échoue faute d'une dépendance optionnelle — un
            # fichier parfaitement valide, refusé. Et une colonne de nombres à zéro initial
            # perdrait ses zéros.
            #
            # Le normaliseur relit de toute façon chaque valeur selon le champ qu'elle
            # alimente (`_whole`, `_moment`) : lui passer le texte d'origine, c'est lui
            # laisser cette décision au lieu de la subir.
            return f"SELECT * FROM read_csv_auto('{escaped_path}', all_varchar=true)"

        if resolved_format == "parquet":
            return f"SELECT * FROM read_parquet('{escaped_path}')"

        raise ValueError(f"Format de fichier non supporté : {resolved_format}")

    @staticmethod
    def _resolve_format(
        path: Path,
        file_format: str | None,
    ) -> str:
        """Détermine le format à partir du paramètre ou de l'extension."""
        if file_format:
            normalized = file_format.lower().lstrip(".")

            if normalized == "json":
                return "jsonl"

            return normalized

        suffix = path.suffix.lower()

        formats = {
            ".jsonl": "jsonl",
            ".json": "jsonl",
            ".csv": "csv",
            ".parquet": "parquet",
        }

        try:
            return formats[suffix]
        except KeyError as exc:
            raise ValueError(f"Impossible de déterminer le format du fichier : {path}") from exc

    @staticmethod
    def _execute(query: str) -> list[dict[str, Any]]:
        """Exécute une requête DuckDB sans créer de stockage persistant."""
        with duckdb.connect() as connection:
            result = connection.execute(query)

            columns = [column[0] for column in result.description]
            rows = result.fetchall()

        return [dict(zip(columns, row, strict=True)) for row in rows]
