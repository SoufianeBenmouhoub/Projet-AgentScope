"""Tests de la répartition des appels d'outils."""

from __future__ import annotations

from agentscope.application.ports.trace_read import TraceFilter
from agentscope.application.use_cases.get_tool_breakdown import GetToolBreakdown
from tests.application.builders import CLAUDE, CODEX, tool_call
from tests.fakes.trace_read import InMemoryTraceRead


def _breakdown(*tool_calls):
    return GetToolBreakdown(InMemoryTraceRead(tool_calls=tool_calls)).execute(TraceFilter())


def test_ordonne_les_outils_du_plus_utilise_au_moins_utilise() -> None:
    result = _breakdown(
        tool_call("s1", tool_name="bash"),
        tool_call("s1", tool_name="read_file"),
        tool_call("s2", tool_name="read_file"),
        tool_call("s2", tool_name="read_file"),
    )

    assert [usage.tool_name for usage in result.usages] == ["read_file", "bash"]
    assert result.usages[0].calls.value == 3
    assert result.distinct_tools == 2


def test_la_part_de_chaque_outil_est_rapportee_au_total() -> None:
    result = _breakdown(
        tool_call("s1", tool_name="bash"),
        tool_call("s1", tool_name="read_file"),
        tool_call("s1", tool_name="read_file"),
        tool_call("s1", tool_name="read_file"),
    )

    assert result.usages[0].share.value == 75.0
    assert result.usages[1].share.value == 25.0


def test_les_parts_totalisent_cent_pour_cent() -> None:
    result = _breakdown(
        tool_call("s1", tool_name="bash"),
        tool_call("s1", tool_name="read_file"),
        tool_call("s2", tool_name="write_file"),
    )

    assert sum(usage.share.value for usage in result.usages) == 100.0


def test_le_taux_derreur_est_calcule_outil_par_outil() -> None:
    result = _breakdown(
        tool_call("s1", tool_name="bash", is_error=True),
        tool_call("s1", tool_name="bash", is_error=False),
        tool_call("s1", tool_name="read_file", is_error=False),
    )

    usages = {usage.tool_name: usage for usage in result.usages}

    assert usages["bash"].error_rate.value == 50.0
    assert usages["read_file"].error_rate.value == 0.0


def test_un_outil_dont_aucune_issue_nest_connue_a_un_taux_indisponible() -> None:
    result = _breakdown(
        tool_call("s1", tool_name="bash", is_error=None),
        tool_call("s1", tool_name="bash", is_error=None),
    )

    assert result.usages[0].error_rate.value is None
    assert result.usages[0].error_rate.total == 2


def test_chaque_outil_porte_les_sessions_ou_il_apparait() -> None:
    """C'est ce qui permet de cliquer sur une barre et de retrouver les sessions."""
    result = _breakdown(
        tool_call("s1", tool_name="bash"),
        tool_call("s2", tool_name="bash"),
        tool_call("s2", tool_name="bash"),
        tool_call("s3", tool_name="read_file"),
    )

    usages = {usage.tool_name: usage for usage in result.usages}

    assert usages["bash"].session_ids == ("s1", "s2")
    assert usages["read_file"].session_ids == ("s3",)


def test_un_perimetre_sans_appel_doutil_donne_une_repartition_vide() -> None:
    result = _breakdown()

    assert result.usages == ()
    assert result.tool_calls_total == 0


def test_le_filtre_par_source_restreint_la_repartition() -> None:
    use_case = GetToolBreakdown(
        InMemoryTraceRead(
            tool_calls=[
                tool_call("s1", source=CLAUDE, tool_name="bash"),
                tool_call("s2", source=CODEX, tool_name="shell"),
            ]
        )
    )

    result = use_case.execute(TraceFilter(sources=(CLAUDE,)))

    assert [usage.tool_name for usage in result.usages] == ["bash"]
    assert result.usages[0].share.value == 100.0
