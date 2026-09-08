"""Tests des routes du dashboard.

L'enjeu de cette couche : que rien de ce que le domaine sait ne se perde en JSON. En
particulier, une mesure indisponible doit arriver au front comme `null`, jamais comme `0`.
"""

from __future__ import annotations

from tests.application.builders import CLAUDE, CODEX, model_call, session, tool_call
from tests.interfaces.client import build_client


def _indicator(payload: dict, key: str) -> dict:
    return next(item for item in payload["indicators"] if item["definition"]["key"] == key)


class TestDefinitions:
    def test_le_catalogue_est_consultable_sans_aucune_donnee_importee(self) -> None:
        response = build_client().get("/api/v1/metrics/definitions")

        assert response.status_code == 200
        definitions = response.json()["definitions"]
        assert len(definitions) >= 4

    def test_chaque_definition_porte_calcul_unite_perimetre_et_valeurs_manquantes(self) -> None:
        """Exigence explicite de l'énoncé, vérifiée jusqu'au contrat exposé au front."""
        definitions = build_client().get("/api/v1/metrics/definitions").json()["definitions"]

        for definition in definitions:
            assert definition["computation"]
            assert definition["unit"]
            assert definition["scope"]
            assert definition["missing_values"]
            assert definition["comparability"] in {"comparable", "source_specific"}


class TestFilterOptions:
    def test_expose_les_valeurs_disponibles_pour_les_filtres(self) -> None:
        client = build_client(
            sessions=[session("s1", source=CLAUDE), session("s2", source=CODEX)],
            model_calls=[model_call("s1", model="claude-opus-5")],
        )

        payload = client.get("/api/v1/metrics/filters").json()

        assert payload["sources"] == [CLAUDE, CODEX]
        assert payload["models"] == ["claude-opus-5"]
        assert payload["first_day"] == "2026-09-01"
        assert payload["is_empty"] is False

    def test_signale_quil_ny_a_rien_a_filtrer_sans_donnees(self) -> None:
        payload = build_client().get("/api/v1/metrics/filters").json()

        assert payload["is_empty"] is True
        assert payload["first_day"] is None


class TestSummary:
    def test_expose_les_indicateurs_avec_leur_definition(self) -> None:
        client = build_client(
            sessions=[session("s1"), session("s2")],
            model_calls=[model_call("s1", input_tokens=100)],
        )

        payload = client.get("/api/v1/metrics/summary").json()

        assert _indicator(payload, "sessions_total")["aggregate"]["value"] == 2
        assert _indicator(payload, "sessions_total")["definition"]["computation"]

    def test_une_mesure_indisponible_arrive_a_null_et_non_a_zero(self) -> None:
        """Le point de rupture le plus probable : une conversion JSON complaisante."""
        client = build_client(
            model_calls=[
                model_call("s1", source=CODEX, cache_creation_tokens=None),
                model_call("s2", source=CODEX, cache_creation_tokens=None),
            ]
        )

        cache = _indicator(client.get("/api/v1/metrics/summary").json(), "cache_creation_tokens")

        assert cache["aggregate"]["value"] is None
        assert cache["aggregate"]["available"] is False

    def test_la_couverture_reelle_est_transmise(self) -> None:
        client = build_client(
            model_calls=[
                model_call("s1", input_tokens=100),
                model_call("s1", input_tokens=None),
            ]
        )

        tokens = _indicator(client.get("/api/v1/metrics/summary").json(), "input_tokens_total")

        assert tokens["aggregate"]["value"] == 100
        assert tokens["aggregate"]["covered"] == 1
        assert tokens["aggregate"]["total"] == 2
        assert tokens["aggregate"]["partial"] is True

    def test_le_melange_de_sources_non_comparables_est_signale(self) -> None:
        client = build_client(
            model_calls=[
                model_call("s1", source=CLAUDE, cache_creation_tokens=500),
                model_call("s2", source=CODEX, cache_creation_tokens=None),
            ]
        )

        payload = client.get("/api/v1/metrics/summary").json()

        assert _indicator(payload, "cache_creation_tokens")["mixes_incomparable_sources"] is True
        assert _indicator(payload, "input_tokens_total")["mixes_incomparable_sources"] is False


class TestFiltres:
    def _client(self):
        return build_client(
            sessions=[
                session("s1", source=CLAUDE, day=1),
                session("s2", source=CODEX, day=5),
            ],
            model_calls=[
                model_call("s1", source=CLAUDE, day=1, input_tokens=100),
                model_call("s2", source=CODEX, day=5, input_tokens=700),
            ],
        )

    def test_sans_filtre_le_perimetre_couvre_tout(self) -> None:
        payload = self._client().get("/api/v1/metrics/summary").json()

        assert _indicator(payload, "input_tokens_total")["aggregate"]["value"] == 800

    def test_le_filtre_par_source_restreint_le_perimetre(self) -> None:
        response = self._client().get("/api/v1/metrics/summary", params={"source": CLAUDE})

        assert _indicator(response.json(), "input_tokens_total")["aggregate"]["value"] == 100

    def test_un_parametre_repete_cumule_les_valeurs(self) -> None:
        response = self._client().get(
            "/api/v1/metrics/summary", params=[("source", CLAUDE), ("source", CODEX)]
        )

        assert _indicator(response.json(), "input_tokens_total")["aggregate"]["value"] == 800

    def test_le_filtre_par_periode_restreint_le_perimetre(self) -> None:
        response = self._client().get(
            "/api/v1/metrics/summary",
            params={"since": "2026-09-04", "until": "2026-09-06"},
        )

        assert _indicator(response.json(), "input_tokens_total")["aggregate"]["value"] == 700

    def test_des_bornes_inversees_sont_refusees_avec_une_explication(self) -> None:
        response = self._client().get(
            "/api/v1/metrics/summary",
            params={"since": "2026-09-10", "until": "2026-09-01"},
        )

        assert response.status_code == 422
        assert "postérieure" in response.json()["detail"]


class TestOutils:
    def test_expose_la_repartition_ordonnee_avec_les_sessions_associees(self) -> None:
        client = build_client(
            tool_calls=[
                tool_call("s1", tool_name="bash"),
                tool_call("s1", tool_name="read_file"),
                tool_call("s2", tool_name="read_file"),
            ]
        )

        payload = client.get("/api/v1/metrics/tools").json()

        assert payload["tool_calls_total"] == 3
        assert payload["distinct_tools"] == 2
        assert payload["usages"][0]["tool_name"] == "read_file"
        assert payload["usages"][0]["session_ids"] == ["s1", "s2"]

    def test_un_perimetre_vide_repond_sans_erreur(self) -> None:
        """Sans données importées, l'API répond « rien », pas une erreur."""
        payload = build_client().get("/api/v1/metrics/tools").json()

        assert payload["usages"] == []
        assert payload["tool_calls_total"] == 0


class TestActivite:
    def test_expose_la_serie_journaliere_avec_les_sessions_de_chaque_point(self) -> None:
        client = build_client(sessions=[session("s1", day=1), session("s2", day=2)])

        payload = client.get("/api/v1/metrics/activity").json()

        assert [point["day"] for point in payload["points"]] == ["2026-09-01", "2026-09-02"]
        assert payload["points"][0]["session_ids"] == ["s1"]

    def test_signale_les_enregistrements_absents_de_la_serie(self) -> None:
        client = build_client(
            sessions=[session("s1", day=1), session("s2", dated=False)],
            tool_calls=[tool_call("s2", dated=False)],
        )

        payload = client.get("/api/v1/metrics/activity").json()

        assert payload["undated_sessions"] == 1
        assert payload["undated_tool_calls"] == 1
        assert payload["has_undated_records"] is True
