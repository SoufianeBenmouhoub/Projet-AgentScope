import { describe, expect, it } from "vitest";

import { buildQueryString } from "./client";

describe("buildQueryString", () => {
  it("encode les filtres répétables et les dates", () => {
    const query = buildQueryString({
      sources: ["traces_lab", "swe_chat"],
      agents: ["claude_code"],
      models: [],
      sessionIds: ["s-1"],
      since: "2025-01-01",
      until: "2025-03-01",
    });

    expect(query).toContain("source=traces_lab");
    expect(query).toContain("source=swe_chat");
    expect(query).toContain("agent=claude_code");
    expect(query).toContain("session_id=s-1");
    expect(query).toContain("since=2025-01-01");
    expect(query).toContain("until=2025-03-01");
  });

  it("retourne une chaîne vide sans filtres", () => {
    expect(buildQueryString()).toBe("");
    expect(buildQueryString({ sources: [], agents: [], models: [], sessionIds: [] })).toBe("");
  });
});
