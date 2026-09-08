/**
 * Tests des transformations qui alimentent les graphiques.
 *
 * Elles sont séparées des composants précisément pour être vérifiables sans DOM ni canvas :
 * ce qui compte ici, c'est que les bonnes valeurs arrivent au bon endroit, pas le rendu.
 */

import { describe, expect, it } from "vitest";

import type { ActivitySeries, ToolBreakdown, ToolUsage } from "../../../shared/api/types";
import { anAggregate } from "../../../test/builders";
import { buildActivityOption, undatedNote } from "./activityOption";
import { buildTokensBySourceOption, missingMeasureNote } from "./tokensBySourceOption";
import { MAX_TOOLS, toBars } from "./toolBreakdownOption";

const THEME = {
  series: ["#2a78d6", "#eb6834", "#1baf7a"] as [string, string, string],
  surface: "#fcfcfb",
  textPrimary: "#0b0b0b",
  textSecondary: "#52514e",
  muted: "#898781",
  gridline: "#e1e0d9",
  axis: "#c3c2b7",
};

function anActivitySeries(overrides: Partial<ActivitySeries> = {}): ActivitySeries {
  return {
    points: [
      { day: "2026-09-01", sessions: 2, model_calls: 10, tool_calls: 5, session_ids: ["s1"] },
      { day: "2026-09-02", sessions: 0, model_calls: 0, tool_calls: 0, session_ids: [] },
    ],
    undated_sessions: 0,
    undated_model_calls: 0,
    undated_tool_calls: 0,
    has_undated_records: false,
    ...overrides,
  };
}

function aToolUsage(name: string, calls: number): ToolUsage {
  return {
    tool_name: name,
    calls: anAggregate({ value: calls, unit: "appels" }),
    share: anAggregate({ value: 10, unit: "%" }),
    error_rate: anAggregate({ value: 0, unit: "%" }),
    median_latency: anAggregate({ value: 100, unit: "ms" }),
    session_ids: ["s1"],
  };
}

describe("courbe d'activité", () => {
  it("expose une série par type d'événement, dans un ordre stable", () => {
    const option = buildActivityOption(anActivitySeries(), THEME);

    expect(option.series.map((serie) => serie.name)).toEqual([
      "Sessions",
      "Appels au modèle",
      "Appels d'outils",
    ]);
    expect(option.series[0].color).toBe(THEME.series[0]);
  });

  it("conserve les journées creuses, qui valent réellement zéro", () => {
    const option = buildActivityOption(anActivitySeries(), THEME);

    expect(option.series[0].data).toEqual([2, 0]);
  });

  it("masque les marqueurs quand les points sont trop nombreux pour rester lisibles", () => {
    const points = Array.from({ length: 40 }, (_, index) => ({
      day: `2026-09-${String((index % 28) + 1).padStart(2, "0")}`,
      sessions: 1,
      model_calls: 1,
      tool_calls: 1,
      session_ids: [],
    }));

    const option = buildActivityOption(anActivitySeries({ points }), THEME);

    expect(option.series[0].showSymbol).toBe(false);
  });

  it("ne dit rien quand tout est horodaté", () => {
    expect(undatedNote(anActivitySeries())).toBeNull();
  });

  it("annonce ce que la courbe ne peut pas montrer", () => {
    const note = undatedNote(
      anActivitySeries({
        undated_sessions: 3,
        undated_tool_calls: 7,
        has_undated_records: true,
      }),
    );

    expect(note).toContain("3 session(s)");
    expect(note).toContain("7 appel(s) d'outil");
    expect(note).not.toContain("appel(s) au modèle");
  });
});

describe("répartition des outils", () => {
  it("garde tous les outils quand ils sont peu nombreux", () => {
    const breakdown: ToolBreakdown = {
      usages: [aToolUsage("bash", 5), aToolUsage("read_file", 3)],
      tool_calls_total: 8,
      distinct_tools: 2,
    };

    expect(toBars(breakdown).map((bar) => bar.name)).toEqual(["bash", "read_file"]);
  });

  it("replie la queue dans « Autres » plutôt que de la tronquer", () => {
    const usages = Array.from({ length: MAX_TOOLS + 5 }, (_, index) =>
      aToolUsage(`outil-${index}`, 100 - index),
    );
    const breakdown: ToolBreakdown = {
      usages,
      tool_calls_total: 1000,
      distinct_tools: usages.length,
    };

    const bars = toBars(breakdown);

    expect(bars).toHaveLength(MAX_TOOLS);
    expect(bars.at(-1)?.name).toContain("Autres");
    expect(bars.at(-1)?.calls).toBe(
      usages.slice(MAX_TOOLS - 1).reduce((total, usage) => total + (usage.calls.value ?? 0), 0),
    );
  });

  it("garde la barre « Autres » cliquable en regroupant les sessions repliées", () => {
    const usages = Array.from({ length: MAX_TOOLS + 2 }, (_, index) => ({
      ...aToolUsage(`outil-${index}`, 100 - index),
      session_ids: [`s${index}`],
    }));
    const breakdown: ToolBreakdown = {
      usages,
      tool_calls_total: 1000,
      distinct_tools: usages.length,
    };

    const autres = toBars(breakdown).at(-1);

    expect(autres?.sessionIds).toEqual(["s10", "s11", "s9"]);
  });

  it("chaque outil porte les sessions où il apparaît", () => {
    const breakdown: ToolBreakdown = {
      usages: [{ ...aToolUsage("bash", 5), session_ids: ["s1", "s2"] }],
      tool_calls_total: 5,
      distinct_tools: 1,
    };

    expect(toBars(breakdown)[0].sessionIds).toEqual(["s1", "s2"]);
  });
});

describe("tokens par source", () => {
  const rows = [
    {
      source: "tracelab-claude",
      inputTokens: anAggregate({ value: 1000, unit: "tokens" }),
      cacheTokens: anAggregate({ value: 500, unit: "tokens" }),
    },
    {
      source: "tracelab-codex",
      inputTokens: anAggregate({ value: 800, unit: "tokens" }),
      cacheTokens: anAggregate({ value: null, unit: "tokens", available: false, covered: 0 }),
    },
  ];

  it("laisse un trou plutôt qu'un zéro là où la mesure n'existe pas", () => {
    const option = buildTokensBySourceOption(rows, THEME);

    expect(option.series[1].data).toEqual([500, null]);
  });

  it("explique qu'une barre absente ne veut pas dire zéro", () => {
    const note = missingMeasureNote(rows);

    expect(note).toContain("tracelab-codex");
    expect(note).toContain("non publié");
  });

  it("ne dit rien quand toutes les sources publient la mesure", () => {
    expect(missingMeasureNote([rows[0]])).toBeNull();
  });
});
