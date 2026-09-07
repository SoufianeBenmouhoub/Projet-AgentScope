"""Schémas de la ressource « système »."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    version: str = Field(description="Version de l'application.")
    database: str = Field(description="État du stockage : « ok » ou « unavailable ».")
    operational: bool = Field(
        description=(
            "Vrai si l'application peut rendre son service. Une application démarrée mais "
            "privée de son stockage est en ligne sans être opérationnelle."
        )
    )
