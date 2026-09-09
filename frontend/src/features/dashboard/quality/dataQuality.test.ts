import { describe, expect, it } from "vitest";

import type { Aggregate, Indicator, KpiSummary } from "../../../shared/api/types";
import { anActivitySeries, anIndicator } from "../../../test/builders";
import {
  partialIndicators,
  toCoverageBySource,
  undatedRecords,
  unavailableIndicators,
} from "./dataQuality";

const aCount = (key: string): Indicator =>
  anIndicator(key, { kind: "count", aggregate: { value: 3, unit: "sessions" } });

const aMeasure = (key: string, aggregate: Partial<Aggregate> = {}): Indicator =>
  anIndicator(key, { kind: "measure", aggregate });

const summaryOf = (indicators: Indicator[]): KpiSummary => ({ indicators });

describe("toCoverageBySource", () => {
  it("ne détaille que les mesures : un dénombrement est complet par construction", () => {
    const summary = summaryOf([
      aCount("sessions_total"),
      aMeasure("input_tokens_total", { value: 100, covered: 4, total: 5, coverage: 0.8 }),
    ]);

    const coverage = toCoverageBySource([{ source: "tracelab-claude", summary }]);

    expect(coverage[0].measures.map((measure) => measure.key)).toEqual(["input_tokens_total"]);
  });

  it("reporte la couverture réelle de chaque mesure", () => {
    const summary = summaryOf([
      aMeasure("input_tokens_total", { value: 100, covered: 4, total: 5, coverage: 0.8 }),
    ]);

    const measure = toCoverageBySource([{ source: "tracelab-claude", summary }])[0].measures[0];

    expect(measure.covered).toBe(4);
    expect(measure.total).toBe(5);
    expect(measure.ratio).toBe(0.8);
    expect(measure.available).toBe(true);
  });

  it("distingue une mesure non publiée d'une mesure à zéro", () => {
    const summary = summaryOf([
      aMeasure("cache_creation_tokens", {
        value: null,
        available: false,
        covered: 0,
        total: 12,
        coverage: 0,
      }),
    ]);

    const measure = toCoverageBySource([{ source: "tracelab-codex", summary }])[0].measures[0];

    expect(measure.available).toBe(false);
    expect(measure.total).toBe(12);
  });

  it("ignore les sources dont la synthèse n'est pas encore arrivée", () => {
    expect(toCoverageBySource([{ source: "tracelab-claude", summary: undefined }])).toEqual([]);
  });
});

describe("unavailableIndicators", () => {
  it("donne la raison de chaque indisponibilité, pas seulement la liste", () => {
    const summary = summaryOf([
      aMeasure("tool_error_rate", { value: null, available: false, covered: 0, total: 9 }),
    ]);

    const entries = unavailableIndicators(summary);

    expect(entries).toHaveLength(1);
    expect(entries[0].reason.length).toBeGreaterThan(0);
  });

  it("ne signale rien quand tout est disponible", () => {
    expect(unavailableIndicators(summaryOf([aMeasure("input_tokens_total")]))).toEqual([]);
  });
});

describe("partialIndicators", () => {
  it("signale un chiffre qui ne porte que sur une partie du périmètre", () => {
    const summary = summaryOf([
      aMeasure("input_tokens_total", {
        value: 100,
        partial: true,
        covered: 3,
        total: 10,
        coverage: 0.3,
      }),
    ]);

    const entries = partialIndicators(summary);

    expect(entries[0].reason).toContain("3");
    expect(entries[0].reason).toContain("10");
  });
});

describe("undatedRecords", () => {
  it("ne liste que ce qui manque réellement", () => {
    const entries = undatedRecords(
      anActivitySeries({ undated_sessions: 2, undated_tool_calls: 5, has_undated_records: true }),
    );

    expect(entries.map((entry) => entry.label)).toEqual(["Sessions", "Appels d'outils"]);
  });

  it("ne dit rien quand tout est horodaté", () => {
    expect(undatedRecords(anActivitySeries())).toEqual([]);
  });
});
