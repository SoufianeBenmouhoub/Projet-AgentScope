import { describe, expect, it } from "vitest";

import { isUnfiltered, NO_FILTERS, toggle, toSearchParams, withPath } from "./filters";

describe("toSearchParams", () => {
  it("ne produit aucun paramètre quand rien n'est filtré", () => {
    expect(toSearchParams(NO_FILTERS).toString()).toBe("");
  });

  it("répète les paramètres à valeurs multiples, comme l'attend l'API", () => {
    const params = toSearchParams({ ...NO_FILTERS, sources: ["b", "a"] });

    expect(params.getAll("source")).toEqual(["a", "b"]);
  });

  it("trie les valeurs pour que deux périmètres identiques donnent la même chaîne", () => {
    const first = toSearchParams({ ...NO_FILTERS, models: ["z", "a"] }).toString();
    const second = toSearchParams({ ...NO_FILTERS, models: ["a", "z"] }).toString();

    expect(first).toBe(second);
  });

  it("transmet les bornes de période", () => {
    const params = toSearchParams({ ...NO_FILTERS, since: "2026-09-01", until: "2026-09-05" });

    expect(params.get("since")).toBe("2026-09-01");
    expect(params.get("until")).toBe("2026-09-05");
  });
});

describe("withPath", () => {
  it("laisse le chemin nu quand aucun filtre n'est actif", () => {
    expect(withPath("/api/v1/metrics/summary", NO_FILTERS)).toBe("/api/v1/metrics/summary");
  });

  it("ajoute la chaîne de requête quand un filtre est actif", () => {
    const path = withPath("/api/v1/metrics/summary", { ...NO_FILTERS, agents: ["codex"] });

    expect(path).toBe("/api/v1/metrics/summary?agent=codex");
  });
});

describe("toggle", () => {
  it("ajoute une valeur absente", () => {
    expect(toggle(["a"], "b")).toEqual(["a", "b"]);
  });

  it("retire une valeur présente", () => {
    expect(toggle(["a", "b"], "a")).toEqual(["b"]);
  });

  it("ne modifie pas la liste d'origine", () => {
    const original = ["a"];

    toggle(original, "b");

    expect(original).toEqual(["a"]);
  });
});

describe("isUnfiltered", () => {
  it("reconnaît l'état d'ouverture du dashboard", () => {
    expect(isUnfiltered(NO_FILTERS)).toBe(true);
  });

  it("détecte une seule borne de période comme un filtre actif", () => {
    expect(isUnfiltered({ ...NO_FILTERS, since: "2026-09-01" })).toBe(false);
  });
});
