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
    path = tmp_path / "traces.csv"
    path.write_text(
        "id,name\n1,Alice\n2,Bob\n",
        encoding="utf-8",
    )

    records = reader.read(path)

    assert records == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


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
