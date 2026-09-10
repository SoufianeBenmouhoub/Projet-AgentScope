"""Tests d'API : la route de proposition de mapping tourne avec la doublure `fake`."""

from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from agentscope.application.ports.mapping_proposal import (
    ImportSample,
    MappingProposal,
    MappingProposalPort,
    MappingProposalUnavailable,
)
from agentscope.application.use_cases.propose_mapping import ProposeMapping
from agentscope.domain.mapping.contract import FIELDS_BY_KEY
from agentscope.interfaces.api.app import create_app
from tests.fakes.mapping_store import InMemoryMappingStore
from tests.interfaces.client import build_client, build_container


def test_propose_un_mapping_a_partir_dechantillons_bruts() -> None:
    response = build_client().post(
        "/api/v1/mapping/propose",
        json={
            "source_format": "jsonl",
            "records": [
                {"session": "sess-1", "tool": "bash"},
                {"session": "sess-2", "tool": "read_file"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()

    names = {m["target_field"] for m in body["mappings"]}
    assert names == {"session", "tool"}
    # La doublure `fake` propose toujours le champ source identique au champ cible.
    assert all(m["source_field"] == m["target_field"] for m in body["mappings"])
    assert all(m["confidence"] == 1.0 for m in body["mappings"])


def test_un_echantillon_vide_repond_sans_erreur() -> None:
    """Aucune donnée importée doit répondre « rien », pas planter."""
    response = build_client().post(
        "/api/v1/mapping/propose",
        json={"source_format": "csv", "records": []},
    )

    assert response.status_code == 200
    assert response.json() == {"mappings": [], "unresolved_notes": []}


class ProviderEnPanne(MappingProposalPort):
    def propose_mapping(self, sample: ImportSample) -> MappingProposal:
        raise MappingProposalUnavailable("Le fournisseur Anthropic n'a pas répondu (401).")


def test_un_fournisseur_injoignable_donne_502_et_non_une_proposition_vide() -> None:
    """« Le service n'a pas répondu » et « aucun champ ne correspond » se ressemblent dans
    une réponse vide. L'utilisateur croirait alors son fichier illisible et corrigerait le
    mauvais problème."""
    container = replace(
        build_container(), propose_mapping=ProposeMapping(mapping_proposal=ProviderEnPanne())
    )
    client = TestClient(create_app(container=container))

    response = client.post(
        "/api/v1/mapping/propose",
        json={"source_format": "jsonl", "records": [{"session": "sess-1"}]},
    )

    assert response.status_code == 502
    assert "Anthropic" in response.json()["detail"]


class TestContrat:
    def test_expose_les_champs_du_modele_commun(self) -> None:
        """L'interface les lit ici plutôt que de les recopier : une liste dupliquée
        finirait par proposer des champs que le moteur refuse."""
        payload = build_client().get("/api/v1/mapping/fields").json()

        keys = {field["key"] for field in payload["fields"]}
        assert keys == set(FIELDS_BY_KEY)

    def test_dit_ce_qui_est_obligatoire_et_a_quoi_chaque_champ_appartient(self) -> None:
        payload = build_client().get("/api/v1/mapping/fields").json()
        by_key = {field["key"]: field for field in payload["fields"]}

        assert by_key["session_id"]["required"] is True
        assert by_key["agent"]["required"] is False
        assert by_key["tool_name"]["scope"] == "tool_call"
        assert by_key["tools"]["scope"] == "collection"
        assert by_key["cache_creation_tokens"]["description"]


class TestEssaiABlanc:
    def test_montre_les_valeurs_lues_et_ce_que_limport_produirait(self) -> None:
        payload = (
            build_client()
            .post(
                "/api/v1/mapping/preview",
                json={
                    "records": [
                        {"sid": "s1", "who": "claude"},
                        {"sid": "s1", "who": "claude"},
                        {"sid": "s2", "who": "codex"},
                    ],
                    "mapping": {"session_id": "sid", "agent": "who"},
                },
            )
            .json()
        )

        assert payload["records"] == 3
        assert payload["sessions"] == 2
        assert payload["model_calls"] == 3
        assert payload["rejected"] == 0

        agent = next(f for f in payload["fields"] if f["target_field"] == "agent")
        assert agent["examples"] == ["claude", "claude", "codex"]
        assert agent["resolved"] == 3

    def test_compte_ce_qui_serait_refuse(self) -> None:
        payload = (
            build_client()
            .post(
                "/api/v1/mapping/preview",
                json={
                    "records": [{"sid": "s1"}, {"autre": "x"}],
                    "mapping": {"session_id": "sid"},
                },
            )
            .json()
        )

        assert payload["rejected"] == 1

    def test_un_mapping_inapplicable_est_refuse_avec_une_explication(self) -> None:
        response = build_client().post(
            "/api/v1/mapping/preview",
            json={"records": [{"sid": "s1"}], "mapping": {"agent": "who"}},
        )

        assert response.status_code == 422
        assert "session_id" in response.json()["detail"]

    def test_lessai_a_blanc_necrit_rien(self) -> None:
        """C'est toute sa raison d'être : vérifier sans avoir à nettoyer ensuite."""
        store = InMemoryMappingStore()
        client = build_client(mapping_store=store)

        client.post(
            "/api/v1/mapping/preview",
            json={"records": [{"sid": "s1"}], "mapping": {"session_id": "sid"}},
        )

        assert store.list_mappings() == ()


class TestBibliotheque:
    def test_enregistre_puis_relit_un_mapping(self) -> None:
        client = build_client()

        saved = client.post(
            "/api/v1/mappings",
            json={
                "name": "TraceLab",
                "source_name": "tracelab",
                "mapping": {"session_id": "session_id", "agent": "provider"},
            },
        ).json()

        assert saved["name"] == "TraceLab"
        assert saved["mapping"]["agent"] == "provider"
        # Les champs écartés sont conservés explicitement, pas absents.
        assert saved["mapping"]["cache_creation_tokens"] is None

        listed = client.get("/api/v1/mappings").json()["mappings"]
        assert [entry["id"] for entry in listed] == [saved["id"]]

    def test_reenregistrer_sous_le_meme_nom_remplace(self) -> None:
        client = build_client()
        body = {"name": "TraceLab", "mapping": {"session_id": "sid"}}

        first = client.post("/api/v1/mappings", json=body).json()
        second = client.post(
            "/api/v1/mappings", json={**body, "mapping": {"session_id": "autre"}}
        ).json()

        assert second["id"] == first["id"]
        assert len(client.get("/api/v1/mappings").json()["mappings"]) == 1

    def test_un_mapping_inapplicable_nest_pas_enregistre(self) -> None:
        client = build_client()

        response = client.post(
            "/api/v1/mappings", json={"name": "Cassé", "mapping": {"agent": "who"}}
        )

        assert response.status_code == 422
        assert client.get("/api/v1/mappings").json() == {"mappings": []}

    def test_un_mapping_sans_nom_est_refuse(self) -> None:
        response = build_client().post(
            "/api/v1/mappings", json={"name": "  ", "mapping": {"session_id": "sid"}}
        )

        assert response.status_code == 422

    def test_supprime_un_mapping_enregistre(self) -> None:
        client = build_client()
        saved = client.post(
            "/api/v1/mappings", json={"name": "TraceLab", "mapping": {"session_id": "sid"}}
        ).json()

        assert client.delete(f"/api/v1/mappings/{saved['id']}").status_code == 204
        assert client.get("/api/v1/mappings").json() == {"mappings": []}

    def test_supprimer_ce_qui_nexiste_pas_donne_404(self) -> None:
        assert build_client().delete("/api/v1/mappings/inconnu").status_code == 404

    def test_une_bibliotheque_vide_repond_sans_erreur(self) -> None:
        assert build_client().get("/api/v1/mappings").json() == {"mappings": []}
