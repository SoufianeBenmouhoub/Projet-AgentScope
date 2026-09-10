"""Tests du choix du fournisseur d'IA dans la racine de composition.

Changer de fournisseur est censé se faire dans `.env`, sans toucher au code. Ces tests
vérifient que c'est vrai, et surtout que les deux façons de mal configurer le projet — un
fournisseur inconnu, un modèle non renseigné — échouent tout de suite avec une phrase
qui dit quoi corriger, plutôt qu'au premier import avec une trace illisible.
"""

from __future__ import annotations

import pytest

from agentscope.composition import build_mapping_proposal
from agentscope.infrastructure.config.settings import Settings
from agentscope.infrastructure.llm.anthropic_api import AnthropicMappingProposal
from agentscope.infrastructure.llm.fake import FakeMappingProposal
from agentscope.infrastructure.llm.ollama import OllamaMappingProposal


def _settings(**overrides) -> Settings:
    # `_env_file=None` isole le test du .env de la machine qui l'exécute.
    return Settings(_env_file=None, **overrides)


def test_la_doublure_est_le_defaut_et_ne_demande_aucune_cle() -> None:
    """C'est ce qui permet à un clone du dépôt de démarrer et de passer ses tests."""
    assert isinstance(build_mapping_proposal(_settings()), FakeMappingProposal)


def test_ollama_est_cable_sur_son_point_dacces_local() -> None:
    adapter = build_mapping_proposal(_settings(ai_provider="ollama", ai_model="un-modele"))

    assert isinstance(adapter, OllamaMappingProposal)


def test_anthropic_est_cable_avec_le_modele_configure() -> None:
    adapter = build_mapping_proposal(
        _settings(ai_provider="anthropic", ai_model="claude-opus-5", ai_api_key="cle-de-test")
    )

    assert isinstance(adapter, AnthropicMappingProposal)


@pytest.mark.parametrize("provider", ["ollama", "anthropic"])
def test_un_fournisseur_reel_sans_modele_est_refuse_avec_un_exemple(provider: str) -> None:
    """Écrire un modèle par défaut dans le code figerait la seule décision que `.env` est
    censé porter, et rendrait la panne illisible le jour où ce modèle disparaît."""
    with pytest.raises(ValueError) as error:
        build_mapping_proposal(_settings(ai_provider=provider, ai_api_key="cle-de-test"))

    assert "AI_MODEL" in str(error.value)


def test_un_fournisseur_inconnu_est_refuse_avec_la_liste_des_valeurs_acceptees() -> None:
    with pytest.raises(ValueError) as error:
        build_mapping_proposal(_settings(ai_provider="mistral", ai_model="un-modele"))

    message = str(error.value)
    assert "mistral" in message
    assert "anthropic" in message and "ollama" in message
