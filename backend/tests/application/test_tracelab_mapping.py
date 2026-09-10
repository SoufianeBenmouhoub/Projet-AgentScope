"""Tests du préréglage de mapping TraceLab."""

from agentscope.application.tracelab import TRACELAB_MAPPING, mapping_for_source
from agentscope.domain.mapping.contract import validate_mapping


def test_le_prereglage_tracelab_est_valide_pour_le_moteur_generique() -> None:
    validate_mapping(TRACELAB_MAPPING)


def test_le_prereglage_est_reconnu_sans_sensibilite_a_la_casse() -> None:
    mapping = mapping_for_source("TraceLab-Claude")

    assert mapping is not None
    assert mapping["agent"] == "provider"


def test_une_source_inconnue_ne_recoit_pas_de_mapping_specifique() -> None:
    assert mapping_for_source("swe-chat") is None


def test_lappelant_recoit_une_copie_modifiable_du_prereglage() -> None:
    mapping = mapping_for_source("tracelab")
    assert mapping is not None

    mapping["model"] = "autre"

    assert TRACELAB_MAPPING["model"] == "model"
