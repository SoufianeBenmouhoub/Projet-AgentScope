"""Tests de l'essai à blanc d'un mapping.

Le normaliseur utilisé ici est le vrai, celui de l'import : c'est la seule façon que
l'aperçu et l'import ne divergent pas. Rien n'est écrit nulle part.
"""

from __future__ import annotations

import pytest

from agentscope.application.use_cases.preview_mapping import PreviewMapping
from agentscope.domain.mapping.contract import InvalidMapping
from agentscope.domain.mapping.field_path import InvalidFieldPath
from agentscope.infrastructure.normalization.record_normalizer import RecordNormalizer

PREVIEW = PreviewMapping(RecordNormalizer())

RECORDS = [
    {
        "sid": "s1",
        "who": "claude",
        "horodatage": "2026-09-01T10:00:00Z",
        "entree": 120,
        "outils": [{"nom": "bash", "echec": True}],
    },
    {
        "sid": "s1",
        "who": "claude",
        "horodatage": "2026-09-01T10:05:00Z",
        "entree": 80,
        "outils": [{"nom": "read"}, {"nom": "edit"}],
    },
    {"sid": "s2", "who": "codex", "horodatage": "2026-09-02T09:00:00Z"},
]

MAPPING = {
    "session_id": "sid",
    "agent": "who",
    "occurred_at": "horodatage",
    "input_tokens": "entree",
    "tools": "outils",
    "tool_name": "nom",
    "tool_is_error": "echec",
}


def _field(preview, key: str):
    return next(field for field in preview.fields if field.target_field == key)


class TestChampParChamp:
    def test_montre_les_valeurs_reellement_lues(self) -> None:
        """Un chemin qui pointe sur la mauvaise colonne rend des valeurs qui ne ressemblent
        pas à ce qu'on attend — ce qu'aucun compteur ne montre."""
        preview = PREVIEW(RECORDS, MAPPING)

        assert _field(preview, "agent").examples == ("claude", "claude", "codex")

    def test_dit_sur_combien_denregistrements_un_champ_est_renseigne(self) -> None:
        preview = PREVIEW(RECORDS, MAPPING)

        entree = _field(preview, "input_tokens")
        assert (entree.resolved, entree.total) == (2, 3)

    def test_un_champ_non_mappe_reste_vide_sans_etre_tu(self) -> None:
        """Il apparaît quand même, avec un chemin nul : c'est ainsi qu'on voit ce qu'on a
        oublié de renseigner."""
        preview = PREVIEW(RECORDS, MAPPING)

        sortie = _field(preview, "output_tokens")
        assert sortie.path is None
        assert sortie.resolved == 0
        assert sortie.examples == ()

    def test_enumere_tout_le_contrat_du_domaine(self) -> None:
        preview = PREVIEW(RECORDS, MAPPING)

        assert {field.target_field for field in preview.fields} >= {
            "session_id",
            "agent",
            "tools",
            "cache_creation_tokens",
        }

    def test_signale_les_champs_obligatoires_et_leur_portee(self) -> None:
        preview = PREVIEW(RECORDS, MAPPING)

        assert _field(preview, "session_id").required is True
        assert _field(preview, "tool_name").scope == "tool_call"

    def test_une_valeur_trop_longue_est_tronquee(self) -> None:
        """Un tableau d'appels d'outils entier ne se lit pas dans une cellule."""
        preview = PREVIEW(
            [{"sid": "s1", "long": "x" * 500}], {"session_id": "sid", "agent": "long"}
        )

        assert _field(preview, "agent").examples[0].endswith("…")


class TestCeQueLimportProduirait:
    def test_compte_les_sessions_apres_regroupement(self) -> None:
        """Trois enregistrements, deux identifiants : deux sessions. C'est le regroupement
        qui compte, pas le nombre de lignes."""
        preview = PREVIEW(RECORDS, MAPPING)

        assert preview.records == 3
        assert preview.sessions == 2
        assert preview.model_calls == 3
        assert preview.tool_calls == 3

    def test_remonte_les_anomalies_sans_les_repeter(self) -> None:
        mapping = {"session_id": "sid", "input_tokens": "who"}

        preview = PREVIEW(RECORDS, mapping)

        assert len(preview.issues) == len(set(preview.issues))
        assert any("n'est pas un nombre entier" in issue for issue in preview.issues)

    def test_compte_les_enregistrements_qui_seraient_refuses(self) -> None:
        preview = PREVIEW([{"sid": "s1"}, {"autre": "x"}], {"session_id": "sid"})

        assert preview.rejected == 1
        assert preview.sessions == 1

    def test_un_echantillon_vide_repond_sans_erreur(self) -> None:
        preview = PREVIEW([], {"session_id": "sid"})

        assert preview.records == 0
        assert preview.sessions == 0
        assert _field(preview, "session_id").total == 0


class TestValidation:
    def test_un_mapping_sans_champ_obligatoire_est_refuse_avant_tout_apercu(self) -> None:
        """Montrer un aperçu bâti sur un mapping que l'import refusera ensuite serait la
        pire des réponses."""
        with pytest.raises(InvalidMapping):
            PREVIEW(RECORDS, {"agent": "who"})

    def test_un_champ_hors_contrat_est_refuse(self) -> None:
        with pytest.raises(InvalidMapping):
            PREVIEW(RECORDS, {"session_id": "sid", "latency_ms": "x"})

    def test_un_chemin_mal_forme_est_refuse(self) -> None:
        with pytest.raises(InvalidFieldPath):
            PREVIEW(RECORDS, {"session_id": "sid", "agent": "outils[["})
