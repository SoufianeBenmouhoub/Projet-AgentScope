from agentscope.application.ports.mapping_proposal import build_import_sample


def test_extrait_les_champs_avec_des_exemples() -> None:
    records = [
        {"session": "sess-1", "tool": "bash"},
        {"session": "sess-2", "tool": "read_file"},
    ]

    sample = build_import_sample(records, source_format="jsonl")

    names = {f.name for f in sample.fields}
    assert names == {"session", "tool"}


def test_limite_le_nombre_de_valeurs_d_exemple() -> None:
    records = [{"x": i} for i in range(10)]

    sample = build_import_sample(records, source_format="jsonl", max_examples=3)

    assert len(sample.fields[0].example_values) == 3
