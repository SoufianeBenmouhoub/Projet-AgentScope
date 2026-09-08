import { describe, expect, it } from "vitest";

import {
  EMPTY_TRACE_FILTERS,
  parseFiltersFromSearchParams,
  writeFiltersToSearchParams,
} from "./filters";

describe("dashboard filters", () => {
  it("lit les filtres depuis l'URL", () => {
    const params = new URLSearchParams();
    params.append("source", "traces_lab");
    params.append("agent", "claude_code");
    params.set("since", "2025-01-01");

    expect(parseFiltersFromSearchParams(params)).toEqual({
      sources: ["traces_lab"],
      agents: ["claude_code"],
      models: [],
      sessionIds: [],
      since: "2025-01-01",
      until: null,
    });
  });

  it("écrit les filtres dans l'URL", () => {
    const params = writeFiltersToSearchParams({
      ...EMPTY_TRACE_FILTERS,
      sources: ["traces_lab"],
      sessionIds: ["s-1"],
      until: "2025-06-01",
    });

    expect(params.getAll("source")).toEqual(["traces_lab"]);
    expect(params.getAll("session_id")).toEqual(["s-1"]);
    expect(params.get("until")).toBe("2025-06-01");
  });
});
