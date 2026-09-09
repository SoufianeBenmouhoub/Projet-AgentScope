import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  aKpiSummary,
  anActivitySeries,
  anEmptyKpiSummary,
  anIndicator,
  aSessionDetail,
  aSessionList,
  aToolBreakdown,
  noFilterOptions,
  someFilterOptions,
} from "../../test/builders";
import { renderWithProviders } from "../../test/renderWithProviders";
import { calledUrls, stubFetch } from "../../test/stubFetch";
import { DashboardPage } from "./DashboardPage";

// jsdom n'a pas de canvas : ECharts est remplacé par un bouton, ce qui permet de vérifier
// le retour d'un graphique vers les sessions sans dépendre du rendu graphique lui-même.
// Les données qui alimentent les graphiques sont testées dans chartOptions.test.ts.
vi.mock("./charts/Chart", () => ({
  Chart: ({ onSelect }: { onSelect?: (click: { dataIndex: number }) => void }) => (
    <button type="button" data-testid="graphique" onClick={() => onSelect?.({ dataIndex: 0 })}>
      graphique
    </button>
  ),
}));

const FILTERS = "/api/v1/metrics/filters";
const SUMMARY = "/api/v1/metrics/summary";
const ACTIVITY = "/api/v1/metrics/activity";
const TOOLS = "/api/v1/metrics/tools";
const SESSION_DETAIL = "/api/v1/sessions/";
const SESSION_LIST = "/api/v1/sessions";

function stubDashboard(summary: unknown, options = someFilterOptions()) {
  return stubFetch([
    { match: FILTERS, body: options },
    { match: ACTIVITY, body: anActivitySeries() },
    { match: TOOLS, body: aToolBreakdown() },
    { match: SUMMARY, body: summary },
    // Le détail avant la liste : « /api/v1/sessions/ » est plus spécifique.
    { match: SESSION_DETAIL, body: aSessionDetail() },
    { match: SESSION_LIST, body: aSessionList() },
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

describe("DashboardPage — visualisations", () => {
  it("affiche les trois graphiques", async () => {
    stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    // Les trois graphiques n'arrivent pas ensemble : celui des tokens attend de connaître
    // la liste des sources avant de pouvoir les interroger une par une.
    await waitFor(() => {
      expect(screen.getByText("Activité dans le temps")).toBeTruthy();
      expect(screen.getByText("Répartition des appels d'outils")).toBeTruthy();
      expect(screen.getByText("Tokens par source")).toBeTruthy();
    });
  });

  it("propose une vue tableau sous chaque graphique", async () => {
    stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Voir les données")).toHaveLength(3);
    });
  });

  it("rend chaque valeur du graphique atteignable dans son tableau", async () => {
    stubDashboard(aKpiSummary());

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("columnheader", { name: "Appels au modèle" })).toBeTruthy();
    });
    expect(screen.getByRole("rowheader", { name: "read_file" })).toBeTruthy();
  });

  it("signale sous la courbe ce qu'elle ne peut pas montrer", async () => {
    stubFetch([
      { match: FILTERS, body: someFilterOptions() },
      {
        match: ACTIVITY,
        body: anActivitySeries({ undated_sessions: 4, has_undated_records: true }),
      },
      { match: TOOLS, body: aToolBreakdown() },
      { match: SUMMARY, body: aKpiSummary() },
      { match: SESSION_DETAIL, body: aSessionDetail() },
      { match: SESSION_LIST, body: aSessionList() },
    ]);

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/faute d'horodatage/i)).toBeTruthy();
    });
  });
});

describe("DashboardPage — retour du graphique vers les sessions", () => {
  async function renderAndClickFirstChart() {
    const fetchMock = stubDashboard(aKpiSummary());
    renderWithProviders(<DashboardPage />);

    await waitFor(() => expect(screen.getAllByTestId("graphique").length).toBeGreaterThan(0));
    await userEvent.click(screen.getAllByTestId("graphique")[0]);

    return fetchMock;
  }

  it("n'interroge pas les sessions tant qu'aucune sélection n'est faite", async () => {
    const fetchMock = stubDashboard(aKpiSummary());
    renderWithProviders(<DashboardPage />);

    await waitFor(() => expect(screen.getAllByTestId("graphique").length).toBeGreaterThan(0));

    expect(calledUrls(fetchMock).some((url) => url.includes(SESSION_LIST))).toBe(false);
  });

  it("affiche les sessions correspondantes après un clic dans un graphique", async () => {
    await renderAndClickFirstChart();

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /sessions sélectionnées/i })).toBeTruthy();
    });
  });

  it("dit d'où vient la sélection", async () => {
    await renderAndClickFirstChart();

    await waitFor(() => {
      expect(screen.getByText(/journée du/i)).toBeTruthy();
    });
  });

  it("repasse les identifiants de sessions en filtre, sans toucher au reste du dashboard", async () => {
    const fetchMock = await renderAndClickFirstChart();

    await waitFor(() => {
      const sessionCalls = calledUrls(fetchMock).filter(
        (url) => url.includes(SESSION_LIST) && !url.includes(SESSION_DETAIL),
      );
      expect(sessionCalls.at(-1)).toContain("session_id=s1");
    });

    // Les indicateurs, eux, restent sur le périmètre complet.
    const summaryCalls = calledUrls(fetchMock).filter((url) => url.includes(SUMMARY));
    expect(summaryCalls.every((url) => !url.includes("session_id"))).toBe(true);
  });

  it("ouvre le détail d'une session choisie dans la liste", async () => {
    await renderAndClickFirstChart();

    await waitFor(() => expect(screen.getByRole("button", { name: "s1" })).toBeTruthy());
    await userEvent.click(screen.getByRole("button", { name: "s1" }));

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /détail de la session s1/i })).toBeTruthy();
    });
    expect(screen.getByText("Chronologie")).toBeTruthy();
  });

  it("affiche « n/a » quand la source ne nomme pas l'agent", async () => {
    stubFetch([
      { match: FILTERS, body: someFilterOptions() },
      { match: ACTIVITY, body: anActivitySeries() },
      { match: TOOLS, body: aToolBreakdown() },
      { match: SUMMARY, body: aKpiSummary() },
      { match: SESSION_DETAIL, body: aSessionDetail({ agent: null }) },
      { match: SESSION_LIST, body: aSessionList() },
    ]);
    renderWithProviders(<DashboardPage />);

    await waitFor(() => expect(screen.getAllByTestId("graphique").length).toBeGreaterThan(0));
    await userEvent.click(screen.getAllByTestId("graphique")[0]);
    await waitFor(() => expect(screen.getByRole("button", { name: "s1" })).toBeTruthy());
    await userEvent.click(screen.getByRole("button", { name: "s1" }));

    await waitFor(() => {
      expect(screen.getByRole("region", { name: /détail de la session s1/i })).toBeTruthy();
    });
    expect(screen.getAllByText("n/a").length).toBeGreaterThan(0);
  });

  it("conserve dans la chronologie un événement non horodaté", async () => {
    await renderAndClickFirstChart();

    await waitFor(() => expect(screen.getByRole("button", { name: "s1" })).toBeTruthy());
    await userEvent.click(screen.getByRole("button", { name: "s1" }));

    await waitFor(() => {
      expect(screen.getByText("non horodatée")).toBeTruthy();
    });
  });

  it("efface la sélection à la demande", async () => {
    await renderAndClickFirstChart();

    await waitFor(() => expect(screen.getByText(/effacer la sélection/i)).toBeTruthy());
    await userEvent.click(screen.getByText(/effacer la sélection/i));

    expect(screen.queryByRole("region", { name: /sessions sélectionnées/i })).toBeNull();
  });
});
