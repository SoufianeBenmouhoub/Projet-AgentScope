"""Tests de la question posée aux modèles et de la relecture de leurs réponses.

Ce module est partagé par les deux fournisseurs réels : ce qui est vérifié ici l'est donc
pour Anthropic comme pour Ollama. Aucun appel réseau.
"""

from __future__ import annotations

from agentscope.application.ports.mapping_proposal import FieldSample, ImportSample
from agentscope.domain.mapping.contract import FIELDS_BY_KEY
from agentscope.infrastructure.llm.prompt import build_prompt, parse_proposal

A_SAMPLE = ImportSample(
    source_format="jsonl",
    fields=(FieldSample(name="session", example_values=("sess-1", "sess-2")),),
)


class TestQuestion:
    def test_la_question_enumere_les_champs_du_contrat_du_domaine(self) -> None:
        """Une liste recopiée dériverait, et le modèle viserait des champs refusés."""
        prompt = build_prompt(A_SAMPLE)

        for key in FIELDS_BY_KEY:
            assert key in prompt

    def test_la_question_montre_des_valeurs_observees(self) -> None:
        """Les noms de champs seuls ne suffisent pas à trancher entre deux candidats."""
        prompt = build_prompt(A_SAMPLE)

        assert "session" in prompt
        assert "sess-1" in prompt

    def test_la_question_signale_les_champs_obligatoires(self) -> None:
        assert "session_id (obligatoire)" in build_prompt(A_SAMPLE)

    def test_la_question_interdit_dinventer_une_correspondance(self) -> None:
        """La règle centrale du projet est dite au modèle, pas seulement au code."""
        prompt = build_prompt(A_SAMPLE)

        assert "null" in prompt
        assert "jamais devenir zéro" in prompt


class TestReponse:
    def test_relit_une_proposition_valide(self) -> None:
        raw = (
            '{"mappings": ['
            '{"target_field": "session_id", "source_field": "session", '
            '"confidence": 0.9, "note": "Nom proche et valeurs cohérentes"}'
            "]}"
        )

        proposal = parse_proposal(raw)

        assert proposal.mappings[0].target_field == "session_id"
        assert proposal.mappings[0].source_field == "session"
        assert proposal.mappings[0].confidence == 0.9
        assert proposal.unresolved_notes == ()

    def test_une_absence_expliquee_remonte_dans_les_notes(self) -> None:
        raw = (
            '{"mappings": [{"target_field": "cache_creation_tokens", "source_field": null, '
            '"confidence": null, "note": "Cette source ne publie pas la mesure"}]}'
        )

        proposal = parse_proposal(raw)

        assert proposal.mappings[0].source_field is None
        assert proposal.unresolved_notes == (
            "cache_creation_tokens : Cette source ne publie pas la mesure",
        )

    def test_un_json_entoure_de_texte_reste_exploitable(self) -> None:
        """Un modèle à qui l'on demande « uniquement du JSON » ajoute souvent un bloc de
        code ou une phrase. Refuser la réponse pour cela seul gaspillerait une proposition
        correcte."""
        raw = (
            "Voici ma proposition :\n```json\n"
            '{"mappings": [{"target_field": "model", "source_field": "model_name", '
            '"confidence": 0.8, "note": "ok"}]}\n```\nBon import !'
        )

        proposal = parse_proposal(raw)

        assert proposal.mappings[0].source_field == "model_name"

    def test_un_champ_hors_du_contrat_est_ecarte_et_signale(self) -> None:
        """L'écarter en silence laisserait croire que le modèle n'a rien proposé pour lui ;
        le garder produirait un mapping que le moteur d'import refuse."""
        raw = (
            '{"mappings": ['
            '{"target_field": "latency_ms", "source_field": "duree", "confidence": 1.0},'
            '{"target_field": "model", "source_field": "model_name", "confidence": 0.8}'
            "]}"
        )

        proposal = parse_proposal(raw)

        assert [item.target_field for item in proposal.mappings] == ["model"]
        assert proposal.unresolved_notes == (
            "latency_ms : champ hors du modèle commun, proposition ignorée.",
        )

    def test_une_reponse_illisible_est_signalee_sans_planter(self) -> None:
        proposal = parse_proposal("pas du json valide")

        assert proposal.mappings == ()
        assert "Réponse IA non exploitable" in proposal.unresolved_notes[0]

    def test_une_reponse_vide_est_signalee_sans_planter(self) -> None:
        """Un modèle peut ne rien renvoyer du tout ; `None` ne doit pas remonter en erreur
        de programmation."""
        proposal = parse_proposal(None)

        assert proposal.mappings == ()
        assert "Réponse IA non exploitable" in proposal.unresolved_notes[0]

    def test_un_json_valide_mais_de_la_mauvaise_forme_est_signale(self) -> None:
        proposal = parse_proposal('{"resultat": "j\'ai bien réfléchi"}')

        assert proposal.mappings == ()
        assert "Réponse IA non exploitable" in proposal.unresolved_notes[0]
