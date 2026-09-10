from pathlib import Path

import pytest

from agentscope.infrastructure.sources.duckdb_file_reader import DuckDBFileReader


@pytest.fixture
def reader() -> DuckDBFileReader:
    return DuckDBFileReader()


def test_read_jsonl(reader: DuckDBFileReader, tmp_path: Path) -> None:
    path = tmp_path / "traces.jsonl"
    path.write_text(
        '{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}\n',
        encoding="utf-8",
    )

    records = reader.read(path)

    assert records == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


def test_read_csv(reader: DuckDBFileReader, tmp_path: Path) -> None:
    """Un CSV est lu tel qu'il est écrit : sans types, donc sans interprétation.

    Le normaliseur relit ensuite chaque valeur selon le champ qu'elle alimente. Laisser
    DuckDB deviner ici ne servirait qu'à décider deux fois, dont une fois trop tôt.
    """
    path = tmp_path / "traces.csv"
    path.write_text(
        "id,name\n1,Alice\n2,Bob\n",
        encoding="utf-8",
    )

    records = reader.read(path)

    assert records == [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]


def test_un_csv_dhorodatages_marques_utc_est_lisible(
    reader: DuckDBFileReader, tmp_path: Path
) -> None:
    """DuckDB en ferait des TIMESTAMP WITH TIME ZONE, dont la conversion vers Python échoue
    faute d'une dépendance optionnelle — un fichier parfaitement valide, refusé."""
    path = tmp_path / "sessions.csv"
    path.write_text(
        "sid,quand\nconv-1,2026-09-01T10:00:00Z\nconv-2,2026-09-02T11:00:00Z\n",
        encoding="utf-8",
    )

    records = reader.read(path)

    assert records[0]["quand"] == "2026-09-01T10:00:00Z"


def test_un_csv_conserve_les_zeros_initiaux(reader: DuckDBFileReader, tmp_path: Path) -> None:
    """Un identifiant « 007 » devenu 7 ne se rattache plus à rien."""
    path = tmp_path / "traces.csv"
    path.write_text("sid\n007\n", encoding="utf-8")

    assert reader.read(path)[0]["sid"] == "007"


def test_read_parquet(reader: DuckDBFileReader, tmp_path: Path) -> None:
    path = tmp_path / "traces.parquet"

    import duckdb

    with duckdb.connect() as connection:
        connection.execute(
            """
            COPY (
                SELECT *
                FROM (
                    VALUES
                        (1, 'Alice'),
                        (2, 'Bob')
                ) AS data(id, name)
            )
            TO ?
            (FORMAT PARQUET)
            """,
            [str(path)],
        )

    records = reader.read(path)

    assert records == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


def test_sample_limits_number_of_records(
    reader: DuckDBFileReader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "traces.jsonl"
    path.write_text(
        '{"id": 1}\n{"id": 2}\n{"id": 3}\n',
        encoding="utf-8",
    )

    records = reader.sample(path, limit=2)

    assert len(records) == 2
    assert records == [
        {"id": 1},
        {"id": 2},
    ]


def test_sample_with_zero_limit_returns_empty(
    reader: DuckDBFileReader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "traces.jsonl"
    path.write_text(
        '{"id": 1}\n',
        encoding="utf-8",
    )

    assert reader.sample(path, limit=0) == []


def test_explicit_format_overrides_extension(
    reader: DuckDBFileReader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "traces.data"
    path.write_text(
        '{"id": 1}\n{"id": 2}\n',
        encoding="utf-8",
    )

    records = reader.read(path, file_format="jsonl")

    assert records == [
        {"id": 1},
        {"id": 2},
    ]


def test_unsupported_format_raises_value_error(
    reader: DuckDBFileReader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "traces.xml"
    path.write_text("<traces />", encoding="utf-8")

    with pytest.raises(ValueError, match="Impossible de déterminer"):
        reader.read(path)


def test_unsupported_explicit_format_raises_value_error(
    reader: DuckDBFileReader,
    tmp_path: Path,
) -> None:
    path = tmp_path / "traces.data"
    path.write_text("whatever", encoding="utf-8")

    with pytest.raises(ValueError, match="Format de fichier non supporté"):
        reader.read(path, file_format="xml")
