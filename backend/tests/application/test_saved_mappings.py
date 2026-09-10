"""Tests de la bibliothèque de mappings : enregistrer, retrouver, supprimer.

C'est ce qui permet de ne pas refaire à chaque import le travail de vérification déjà fait
une fois.
"""

from __future__ import annotations

import pytest

from agentscope.application.use_cases.delete_mapping import DeleteMapping, MappingNotFound
from agentscope.application.use_cases.list_mappings import ListMappings
from agentscope.application.use_cases.save_mapping import SaveMapping
from agentscope.domain.mapping.contract import FIELDS_BY_KEY, InvalidMapping
from agentscope.domain.mapping.field_path import InvalidFieldPath
from tests.fakes.mapping_store import InMemoryMappingStore

A_MAPPING = {"session_id": "sid", "agent": "who"}


class TestEnregistrer:
    def test_conserve_un_mapping_sous_son_nom(self) -> None:
        store = InMemoryMappingStore()

        saved = SaveMapping(store)("TraceLab", A_MAPPING, source_name="tracelab")

        assert saved.name == "TraceLab"
        assert saved.source_name == "tracelab"
        assert saved.fields["session_id"] == "sid"

    def test_conserve_aussi_les_champs_laisses_vides(self) -> None:
        """Relire un mapping doit dire ce qui a été délibérément écarté, pas seulement ce
        qui a été rempli."""
        store = InMemoryMappingStore()

        saved = SaveMapping(store)("TraceLab", A_MAPPING)

        assert set(saved.fields) == set(FIELDS_BY_KEY)
        assert saved.fields["cache_creation_tokens"] is None

    def test_reenregistrer_sous_le_meme_nom_remplace(self) -> None:
        """Corriger un mapping consiste à le réenregistrer. Laisser s'accumuler
        « tracelab », « tracelab 2 », « tracelab final » ne rendrait service à personne."""
        store = InMemoryMappingStore()
        save = SaveMapping(store)

        first = save("TraceLab", A_MAPPING)
        second = save("TraceLab", {"session_id": "autre_sid"})

        assert second.mapping_id == first.mapping_id
        assert second.fields["session_id"] == "autre_sid"
        assert len(store.list_mappings()) == 1

    def test_les_espaces_autour_du_nom_sont_retires(self) -> None:
        store = InMemoryMappingStore()

        assert SaveMapping(store)("  TraceLab  ", A_MAPPING).name == "TraceLab"

    def test_un_nom_vide_est_refuse(self) -> None:
        with pytest.raises(InvalidMapping):
            SaveMapping(InMemoryMappingStore())("   ", A_MAPPING)

    def test_un_mapping_inapplicable_nest_pas_conserve(self) -> None:
        """Conservé aujourd'hui, il deviendrait une panne inexplicable le jour où quelqu'un
        le rechargerait, sur un autre fichier, sans se souvenir de rien."""
        store = InMemoryMappingStore()

        with pytest.raises(InvalidMapping):
            SaveMapping(store)("Sans identifiant", {"agent": "who"})

        assert store.list_mappings() == ()

    def test_un_chemin_mal_forme_nest_pas_conserve(self) -> None:
        store = InMemoryMappingStore()

        with pytest.raises(InvalidFieldPath):
            SaveMapping(store)("Chemin cassé", {"session_id": "sid", "agent": "a[["})

        assert store.list_mappings() == ()


class TestLister:
    def test_rend_le_plus_recemment_modifie_en_premier(self) -> None:
        """C'est l'ordre de l'usage : celui qu'on vient de mettre au point est presque
        toujours celui qu'on veut rejouer."""
        store = InMemoryMappingStore()
        save = SaveMapping(store)
        save("Ancien", A_MAPPING)
        save("Récent", A_MAPPING)

        assert [saved.name for saved in ListMappings(store)()] == ["Récent", "Ancien"]

    def test_une_bibliotheque_vide_reste_vide(self) -> None:
        assert ListMappings(InMemoryMappingStore())() == ()


class TestSupprimer:
    def test_retire_le_mapping_de_la_bibliotheque(self) -> None:
        store = InMemoryMappingStore()
        saved = SaveMapping(store)("TraceLab", A_MAPPING)

        DeleteMapping(store)(saved.mapping_id)

        assert store.list_mappings() == ()

    def test_supprimer_ce_qui_nexiste_pas_est_signale(self) -> None:
        """Croire avoir supprimé un mapping qui existe toujours mène à le retrouver plus
        tard sans comprendre pourquoi."""
        with pytest.raises(MappingNotFound):
            DeleteMapping(InMemoryMappingStore())("inconnu")
