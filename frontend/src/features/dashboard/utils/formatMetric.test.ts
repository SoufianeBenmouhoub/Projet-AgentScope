import { describe, expect, it } from "vitest";

import type { AggregateResponse } from "../../../shared/api/types";
import {
  formatAggregateValue,
  formatCoverage,
  isAggregateAvailable,
} from "./formatMetric";

function aggregate(partial: Partial<AggregateResponse>): AggregateResponse {
  return {
    value: null,
    unit: "tokens",
    available: false,
    partial: false,
    covered: 0,
    total: 0,
    coverage: null,
    ...partial,
  };
}

describe("formatMetric", () => {
  it("affiche un tiret quand la mesure est indisponible", () => {
    expect(formatAggregateValue(aggregate({ available: false, value: 0 }))).toBe("—");
    expect(isAggregateAvailable(aggregate({ available: true, value: null }))).toBe(false);
  });

  it("formate les pourcentages et les entiers", () => {
    expect(
      formatAggregateValue(
        aggregate({ available: true, value: 42.5, unit: "%", covered: 10, total: 10 }),
      ),
    ).toBe("42,5 %");

    expect(
      formatAggregateValue(
        aggregate({ available: true, value: 1200, unit: "tokens", covered: 5, total: 5 }),
      ),
    ).toMatch(/1[\s\u202f]?200/);
  });

  it("formate la couverture", () => {
    expect(formatCoverage(aggregate({ coverage: 0.75, total: 4, covered: 3 }))).toBe("75 %");
    expect(formatCoverage(aggregate({ coverage: null, total: 0, covered: 0 }))).toBeNull();
  });
});
