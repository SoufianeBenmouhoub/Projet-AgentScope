import { describe, expect, it } from "vitest";

import type { Aggregate } from "../../shared/api/types";
import { coverageNote, formatAggregate, UNAVAILABLE } from "./formatting";

/**
 * Remplace les espaces insécables fines produites par la mise en forme française par des
 * espaces ordinaires, pour que les attentes des tests restent lisibles.
 */
function normalize(text: string): string {
  return text.replace(/[  ]/g, " ");
}

function aggregate(overrides: Partial<Aggregate> = {}): Aggregate {
  return {
    value: 100,
    unit: "tokens",
    available: true,
    partial: false,
    covered: 10,
    total: 10,
    coverage: 1,
    ...overrides,
  };
}

describe("formatAggregate", () => {
  it("n'affiche jamais zéro pour une mesure indisponible", () => {
    const result = formatAggregate(aggregate({ value: null, available: false, covered: 0 }));

    expect(result).toBe(UNAVAILABLE);
    expect(result).not.toContain("0");
  });

  it("affiche zéro quand la valeur est réellement zéro", () => {
    expect(formatAggregate(aggregate({ value: 0, unit: "sessions" }))).toBe("0 sessions");
  });

  it("met en forme les pourcentages avec une décimale", () => {
    expect(formatAggregate(aggregate({ value: 25, unit: "%" }))).toBe("25,0 %");
  });

  it("met en forme les durées en millisecondes", () => {
    expect(normalize(formatAggregate(aggregate({ value: 1250, unit: "ms" })))).toBe("1 250 ms");
  });
});

describe("coverageNote", () => {
  it("ne dit rien quand la valeur porte sur tout le périmètre", () => {
    expect(coverageNote(aggregate())).toBeNull();
  });

  it("explique pourquoi une mesure est indisponible malgré des enregistrements", () => {
    const note = coverageNote(aggregate({ value: null, available: false, covered: 0, total: 8 }));

    expect(note).toContain("8");
    expect(note).toContain("renseigne");
  });

  it("distingue un périmètre vide d'une mesure jamais renseignée", () => {
    const note = coverageNote(
      aggregate({ value: null, available: false, covered: 0, total: 0, coverage: null }),
    );

    expect(note).toBe("Aucun enregistrement dans le périmètre.");
  });

  it("signale une couverture partielle avec sa proportion", () => {
    const note = coverageNote(
      aggregate({ value: 100, partial: true, covered: 3, total: 10, coverage: 0.3 }),
    );

    expect(note).toContain("3");
    expect(note).toContain("10");
    expect(note).toContain("30,0 %");
  });
});
