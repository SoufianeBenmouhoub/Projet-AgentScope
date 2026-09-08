import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { aKpiSummary, anEmptyKpiSummary, anIndicator } from "../../test/builders";
import { renderWithProviders } from "../../test/renderWithProviders";
import { DashboardPage } from "./DashboardPage";

function stubApi(body: unknown, { ok = true }: { ok?: boolean } = {}) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok, json: async () => body }));
}

describe("DashboardPage", () => {
  it("affiche les indicateurs renvoyés par l'API", async () => {
    stubApi(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("12 sessions")).toBeTruthy();
    });
    expect(screen.getByText("340 appels")).toBeTruthy();
  });

  it("annonce qu'aucune trace n'a été importée au lieu d'afficher des indicateurs à zéro", async () => {
    stubApi(anEmptyKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/aucune trace n'a encore été importée/i)).toBeTruthy();
    });
  });

  it("affiche « n/a » et non « 0 » pour une mesure indisponible", async () => {
    stubApi(
      aKpiSummary([
        anIndicator("cache_creation_tokens", {
          aggregate: {
            value: null,
            unit: "tokens",
            available: false,
            covered: 0,
            total: 40,
            coverage: 0,
          },
        }),
      ]),
    );

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("n/a")).toBeTruthy();
    });
    expect(screen.getByText(/ne renseigne cette mesure/i)).toBeTruthy();
  });

  it("signale un indicateur qui mélange des sources non comparables", async () => {
    stubApi(
      aKpiSummary([
        anIndicator("cache_creation_tokens", {
          aggregate: { value: 500, unit: "tokens" },
          indicator: {
            sources: ["tracelab-claude", "tracelab-codex"],
            mixes_incomparable_sources: true,
          },
        }),
      ]),
    );

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/ne le mesurent pas de la même façon/i)).toBeTruthy();
    });
  });

  it("rend la définition de chaque indicateur consultable", async () => {
    stubApi(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Définition").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Calcul de sessions_total.")).toBeTruthy();
  });

  it("signale une API injoignable au lieu d'afficher un tableau vide", async () => {
    stubApi({}, { ok: false });

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });
});
