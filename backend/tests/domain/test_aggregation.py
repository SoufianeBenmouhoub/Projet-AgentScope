"""Tests de la règle centrale : une donnée indisponible ne devient jamais un zéro."""

from __future__ import annotations

import pytest

from agentscope.domain.metrics.aggregation import (
    Aggregate,
    count_of,
    median_of,
    rate_of,
    sum_of,
)


class TestSumOf:
    def test_somme_les_valeurs_renseignees(self) -> None:
        result = sum_of([10, 20, 30], unit="tokens")

        assert result.value == 60
        assert result.covered == 3
        assert result.total == 3
        assert result.is_partial is False

    def test_ignore_les_valeurs_absentes_et_signale_la_couverture(self) -> None:
        result = sum_of([10, None, 30, None], unit="tokens")

        assert result.value == 40
        assert result.covered == 2
        assert result.total == 4
        assert result.coverage == 0.5
        assert result.is_partial is True

    def test_une_mesure_jamais_renseignee_est_indisponible_et_non_nulle(self) -> None:
        result = sum_of([None, None], unit="tokens")

        assert result.value is None
        assert result.is_available is False
        assert result.covered == 0

    def test_un_perimetre_vide_est_indisponible(self) -> None:
        result = sum_of([], unit="tokens")

        assert result.value is None
        assert result.coverage is None


class TestMedianOf:
    def test_prend_la_mediane_des_valeurs_renseignees(self) -> None:
        result = median_of([10, 1000, 20], unit="ms")

        assert result.value == 20

    def test_resiste_aux_valeurs_extremes_contrairement_a_une_moyenne(self) -> None:
        result = median_of([10, 12, 14, 16, 100000], unit="ms")

        assert result.value == 14

    def test_une_serie_sans_mesure_est_indisponible(self) -> None:
        assert median_of([None, None], unit="ms").value is None


class TestCountOf:
    def test_un_denombrement_nul_est_une_vraie_valeur(self) -> None:
        result = count_of(0, unit="sessions")

        assert result.value == 0
        assert result.is_available is True

    def test_refuse_un_denombrement_negatif(self) -> None:
        with pytest.raises(ValueError, match="négatif"):
            count_of(-1, unit="sessions")


class TestRateOf:
    def test_rapporte_aux_seuls_cas_observes(self) -> None:
        # 2 erreurs sur 8 appels dont l'issue est connue, parmi 10 appels au total.
        result = rate_of(matching=2, observed=8, population=10)

        assert result.value == 25.0
        assert result.covered == 8
        assert result.total == 10

    def test_ne_compte_pas_les_cas_inconnus_comme_des_succes(self) -> None:
        """Le piège classique : diviser par la population sous-estime le taux."""
        result = rate_of(matching=2, observed=8, population=10)

        assert result.value != 20.0

    def test_sans_aucun_cas_observe_le_taux_est_indisponible(self) -> None:
        result = rate_of(matching=0, observed=0, population=10)

        assert result.value is None
        assert result.total == 10

    def test_refuse_plus_de_cas_verifiants_que_de_cas_observes(self) -> None:
        with pytest.raises(ValueError, match="observés"):
            rate_of(matching=5, observed=2, population=10)


class TestAggregate:
    def test_refuse_une_couverture_superieure_au_perimetre(self) -> None:
        with pytest.raises(ValueError, match="périmètre"):
            Aggregate(value=1.0, unit="tokens", covered=5, total=2)
