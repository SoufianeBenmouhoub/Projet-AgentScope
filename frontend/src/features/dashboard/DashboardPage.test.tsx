import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  aKpiSummary,
  anEmptyKpiSummary,
  anIndicator,
  noFilterOptions,
  someFilterOptions,
} from "../../test/builders";
import { renderWithProviders } from "../../test/renderWithProviders";
import { calledUrls, stubFetch } from "../../test/stubFetch";
import { DashboardPage } from "./DashboardPage";

const FILTERS = "/api/v1/metrics/filters";
const SUMMARY = "/api/v1/metrics/summary";

function stubDashboard(summary: unknown, options = someFilterOptions()) {
  return stubFetch([
    { match: FILTERS, body: options },
    { match: SUMMARY, body: summary },
  ]);
}

describe("DashboardPage", () => {
  it("affiche les indicateurs renvoyés par l'API", async () => {
    stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("12 sessions")).toBeTruthy();
    });
    expect(screen.getByText("340 appels")).toBeTruthy();
  });

  it("annonce qu'aucune trace n'a été importée au lieu d'afficher des indicateurs à zéro", async () => {
    stubDashboard(anEmptyKpiSummary(), noFilterOptions());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/aucune trace n'a encore été importée/i)).toBeTruthy();
    });
  });

  it("distingue un périmètre vidé par les filtres d'une absence d'import", async () => {
    stubDashboard(anEmptyKpiSummary(), someFilterOptions());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/aucune trace à afficher/i)).toBeTruthy();
    });
    expect(screen.queryByText(/aucune trace n'a encore été importée/i)).toBeNull();
  });

  it("affiche « n/a » et non « 0 » pour une mesure indisponible", async () => {
    stubDashboard(
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
    stubDashboard(
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
    stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Définition").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Calcul de sessions_total.")).toBeTruthy();
  });

  it("signale une API injoignable au lieu d'afficher un tableau vide", async () => {
    stubFetch([
      { match: FILTERS, body: someFilterOptions() },
      { match: SUMMARY, body: {}, ok: false },
    ]);

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });
});

describe("DashboardPage — filtres", () => {
  it("propose les valeurs réellement présentes dans les traces", async () => {
    stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("tracelab-claude")).toBeTruthy();
    });
    expect(screen.getByLabelText("claude-opus-5")).toBeTruthy();
  });

  it("transmet le filtre choisi à l'API", async () => {
    const fetchMock = stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);
    await waitFor(() => expect(screen.getByLabelText("tracelab-codex")).toBeTruthy());

    await userEvent.click(screen.getByLabelText("tracelab-codex"));

    await waitFor(() => {
      const summaryCalls = calledUrls(fetchMock).filter((url) => url.includes(SUMMARY));
      expect(summaryCalls.at(-1)).toContain("source=tracelab-codex");
    });
  });

  it("n'affiche pas de calendrier quand aucun enregistrement n'est horodaté", async () => {
    stubDashboard(aKpiSummary(), someFilterOptions({ first_day: null, last_day: null }));

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/le filtre par période ne s'applique pas/i)).toBeTruthy();
    });
  });

  it("masque les filtres tant qu'aucune trace n'est importée", async () => {
    stubDashboard(anEmptyKpiSummary(), noFilterOptions());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/aucune trace n'a encore été importée/i)).toBeTruthy();
    });
    expect(screen.queryByRole("form", { name: /filtres/i })).toBeNull();
  });
});
