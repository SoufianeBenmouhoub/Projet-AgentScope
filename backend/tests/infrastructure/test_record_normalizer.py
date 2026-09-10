"""Tests du normaliseur piloté par mapping.

Le normaliseur ne connaît aucune source en particulier : tout ce qu'il sait faire, il le
fait à partir du mapping qu'on lui donne. C'est ce qui permet d'intégrer une nouvelle
source par configuration plutôt qu'en écrivant un connecteur.
"""

from datetime import datetime
from typing import Any

from agentscope.application.ports.normalization import NormalizedRecord
from agentscope.infrastructure.normalization.record_normalizer import RecordNormalizer

MAPPING: dict[str, str | None] = {
    "session_id": "conversation_id",
    "agent": "agent_name",
    "occurred_at": "start_time",
    "ended_at": "end_time",
}


def normalize(record: dict[str, Any], mapping: dict[str, str | None] | None = None):
    return RecordNormalizer().normalize(
        record=record, mapping=mapping or MAPPING, source="test-dataset"
    )


class TestSession:
    def test_traduit_un_enregistrement_vers_le_modele_commun(self) -> None:
        result = normalize(
            {
                "conversation_id": "session-123",
                "agent_name": "test-agent",
                "start_time": "2026-09-08T10:30:00+00:00",
                "end_time": "2026-09-08T10:35:00+00:00",
            }
        )

        assert isinstance(result, NormalizedRecord)
        session = result.sessions[0]
        assert session.external_id == "session-123"
        assert session.source == "test-dataset"
        assert session.agent_name == "test-agent"
        assert session.started_at == datetime.fromisoformat("2026-09-08T10:30:00+00:00")
        assert session.ended_at == datetime.fromisoformat("2026-09-08T10:35:00+00:00")
        assert result.issues == []

    def test_sans_identifiant_de_session_rien_nest_produit(self) -> None:
        """C'est le seul champ dont l'absence est rédhibitoire : sans lui, un enregistrement
        ne peut être rattaché à rien."""
        result = normalize({"agent_name": "test-agent", "start_time": "2026-09-08T10:30:00Z"})

        assert result.sessions == []
        assert result.model_calls == []
        assert any(issue.field == "session_id" for issue in result.issues)

    def test_un_agent_non_nomme_ne_fait_pas_perdre_lenregistrement(self) -> None:
        """Toutes les sources ne nomment pas l'agent. Écarter la session pour autant
        reviendrait à jeter des données parfaitement exploitables."""
        result = normalize({"conversation_id": "session-123", "start_time": "2026-09-08T10:30:00Z"})

        assert len(result.sessions) == 1
        assert result.sessions[0].agent_name is None

    def test_une_date_absente_nest_pas_une_anomalie(self) -> None:
        """Beaucoup de sources ne datent pas tout. Le tableau de bord compte à part ce qui
        n'est pas horodaté ; le signaler ici noierait les vraies anomalies."""
        result = normalize({"conversation_id": "session-123"})

        assert result.sessions[0].started_at is None
        assert result.issues == []

    def test_une_date_illisible_est_signalee(self) -> None:
        """Présente mais incompréhensible : là, il y a quelque chose à dire."""
        result = normalize({"conversation_id": "session-123", "start_time": "pas-une-date"})

        assert result.sessions[0].started_at is None
        assert any(issue.field == "occurred_at" for issue in result.issues)


class TestModelCall:
    def test_produit_un_appel_au_modele_rattache_a_sa_session(self) -> None:
        mapping = MAPPING | {
            "model": "model",
            "input_tokens": "tokens_in",
            "output_tokens": "tokens_out",
        }

        result = normalize(
            {
                "conversation_id": "s1",
                "model": "claude-opus-5",
                "tokens_in": 1200,
                "tokens_out": 300,
            },
            mapping,
        )

        call = result.model_calls[0]
        assert call.session_id == result.sessions[0].id
        assert call.model_name == "claude-opus-5"
        assert call.input_tokens == 1200
        assert call.output_tokens == 300

    def test_un_compteur_non_mappe_reste_absent_et_non_nul(self) -> None:
        result = normalize({"conversation_id": "s1"})

        assert result.model_calls[0].input_tokens is None

    def test_un_compteur_illisible_est_signale_et_laisse_absent(self) -> None:
        """Mieux vaut un indicateur qui se déclare partiel qu'un chiffre fabriqué."""
        result = normalize(
            {"conversation_id": "s1", "n": "beaucoup"}, MAPPING | {"input_tokens": "n"}
        )

        assert result.model_calls[0].input_tokens is None
        assert any(issue.field == "input_tokens" for issue in result.issues)


class TestCheminsImbriques:
    def test_descend_dans_une_structure_imbriquee(self) -> None:
        """Les traces réelles ne sont pas plates : sans cela, TraceLab serait illisible."""
        result = normalize(
            {
                "conversation_id": "s1",
                "events": [{"timestamp": "2026-09-08T10:30:00Z"}, {"timestamp": "plus tard"}],
            },
            MAPPING | {"occurred_at": "events[0].timestamp"},
        )

        assert result.sessions[0].started_at == datetime.fromisoformat("2026-09-08T10:30:00+00:00")

    def test_un_chemin_qui_ne_mene_nulle_part_rend_une_absence(self) -> None:
        result = normalize(
            {"conversation_id": "s1"}, MAPPING | {"occurred_at": "events[3].timestamp"}
        )

        assert result.sessions[0].started_at is None
        assert result.issues == []


class TestToolCalls:
    MAPPING_WITH_TOOLS = MAPPING | {
        "tools": "tools",
        "tool_name": "tool_name",
        "tool_is_error": "is_error",
        "tool_started_at": "emitted_at",
        "tool_ended_at": "result_at",
    }

    def test_produit_un_appel_par_element_du_tableau(self) -> None:
        result = normalize(
            {
                "conversation_id": "s1",
                "tools": [
                    {"tool_name": "Bash", "is_error": False},
                    {"tool_name": "Read", "is_error": True},
                ],
            },
            self.MAPPING_WITH_TOOLS,
        )

        assert [call.tool_name for call in result.tool_calls] == ["Bash", "Read"]
        assert [call.is_error for call in result.tool_calls] == [False, True]
        assert all(call.session_id == result.sessions[0].id for call in result.tool_calls)

    def test_une_issue_non_publiee_reste_inconnue(self) -> None:
        """« On ne sait pas » n'est pas « réussi » : le taux d'erreur l'exclut de son
        dénominateur plutôt que de le compter comme un succès."""
        result = normalize(
            {"conversation_id": "s1", "tools": [{"tool_name": "Bash"}]},
            self.MAPPING_WITH_TOOLS,
        )

        assert result.tool_calls[0].is_error is None

    def test_une_source_sans_outils_nest_pas_une_anomalie(self) -> None:
        result = normalize({"conversation_id": "s1"}, self.MAPPING_WITH_TOOLS)

        assert result.tool_calls == []
        assert result.issues == []

    def test_un_chemin_qui_ne_designe_pas_une_liste_est_signale(self) -> None:
        result = normalize(
            {"conversation_id": "s1", "tools": "Bash"},
            self.MAPPING_WITH_TOOLS,
        )

        assert result.tool_calls == []
        assert any(issue.field == "tools" for issue in result.issues)

    def test_sans_mapping_doutils_le_tableau_est_ignore(self) -> None:
        result = normalize({"conversation_id": "s1", "tools": [{"tool_name": "Bash"}]})

        assert result.tool_calls == []
