"""Cas d'utilisation : conserver un mapping vérifié pour le rejouer plus tard."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.ports.mapping_store import MappingStorePort, SavedMapping
from agentscope.domain.mapping.contract import FIELDS_BY_KEY, InvalidMapping, validate_mapping


@dataclass(frozen=True)
class SaveMapping:
    """Enregistre un mapping sous un nom, après l'avoir validé.

    La validation à l'enregistrement n'est pas une redite de celle de l'import : un mapping
    inapplicable conservé aujourd'hui deviendrait une panne inexplicable le jour où
    quelqu'un le rechargerait, sur un autre fichier, sans se souvenir de rien.
    """

    store: MappingStorePort

    def __call__(
        self, name: str, fields: dict[str, str | None], source_name: str | None = None
    ) -> SavedMapping:
        clean = name.strip()
        if not clean:
            raise InvalidMapping("Un mapping enregistré doit porter un nom.")

        validate_mapping(fields)

        # On conserve la liste complète des champs, y compris ceux laissés vides : relire un
        # mapping doit dire ce qui a été délibérément écarté, pas seulement ce qui a été
        # rempli.
        complete = {key: fields.get(key) for key in FIELDS_BY_KEY}

        return self.store.save(
            name=clean,
            source_name=(source_name or "").strip() or None,
            fields=complete,
        )
