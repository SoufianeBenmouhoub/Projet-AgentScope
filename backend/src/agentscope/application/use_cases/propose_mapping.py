"""Cas d'utilisation : proposer un mapping pour un échantillon de données importé."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.ports.mapping_proposal import (
    ImportSample,
    MappingProposal,
    MappingProposalPort,
)


@dataclass(frozen=True)
class ProposeMapping:
    """Analyse un échantillon et propose une correspondance vers le modèle du domaine."""

    mapping_proposal: MappingProposalPort

    def __call__(self, sample: ImportSample) -> MappingProposal:
        return self.mapping_proposal.propose_mapping(sample)