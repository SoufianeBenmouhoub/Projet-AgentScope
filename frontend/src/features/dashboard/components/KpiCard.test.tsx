import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { IndicatorResponse } from "../../../shared/api/types";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { KpiCard } from "./KpiCard";

const availableIndicator: IndicatorResponse = {
  definition: {
    key: "sessions_total",
    label: "Sessions",
    unit: "sessions",
    computation: "Nombre de sessions.",
    scope: "Périmètre filtré.",
    missing_values: "Toujours disponible.",
    comparability: "comparable",
  },
  aggregate: {
    value: 12,
    unit: "sessions",
    available: true,
    partial: false,
    covered: 12,
    total: 12,
    coverage: 1,
  },
  sources: ["traces_lab"],
  mixes_incomparable_sources: false,
};

const unavailableIndicator: IndicatorResponse = {
  ...availableIndicator,
  definition: {
    ...availableIndicator.definition,
    key: "input_tokens_total",
    label: "Tokens en entrée",
    unit: "tokens",
  },
  aggregate: {
    value: null,
    unit: "tokens",
    available: false,
    partial: false,
    covered: 0,
    total: 5,
    coverage: 0,
  },
  sources: [],
};

describe("KpiCard", () => {
  it("affiche la valeur quand la mesure est disponible", () => {
    renderWithProviders(<KpiCard indicator={availableIndicator} />);

    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Sessions" })).toBeTruthy();
  });

  it("signale l'indisponibilité au lieu d'afficher zéro", () => {
    renderWithProviders(<KpiCard indicator={unavailableIndicator} />);

    expect(screen.getByText("—")).toBeTruthy();
    expect(screen.getByText(/indisponible/i)).toBeTruthy();
    expect(screen.queryByText(/^0$/)).toBeNull();
  });

  it("affiche la définition au clic sur le bouton d'aide", () => {
    renderWithProviders(<KpiCard indicator={availableIndicator} />);

    fireEvent.click(screen.getByRole("button", { name: /voir la définition/i }));

    expect(screen.getByText(/nombre de sessions/i)).toBeTruthy();
    expect(screen.getByText(/périmètre filtré/i)).toBeTruthy();
  });
});
