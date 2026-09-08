"""Doublure de test pour le port de proposition de mapping. Aucun appel réseau."""

from __future__ import annotations

from agentscope.application.ports.mapping_proposal import (
    FieldMapping,
    ImportSample,
    MappingProposal,
    MappingProposalPort,
)


class FakeMappingProposal(MappingProposalPort):
    """Renvoie une correspondance triviale (nom identique), pour les tests automatisés."""

    def propose_mapping(self, sample: ImportSample) -> MappingProposal:
        mappings = tuple(
            FieldMapping(
                target_field=field.name,
                source_field=field.name,
                confidence=1.0,
            )
            for field in sample.fields
        )
        return MappingProposal(mappings=mappings)
