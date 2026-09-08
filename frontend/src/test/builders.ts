/**
 * Constructeurs de réponses d'API pour les tests du front.
 *
 * Ces données sont **fictives et réservées aux tests** : le dashboard livré n'affiche que
 * des données réellement importées.
 */

import type { Aggregate, Indicator, KpiSummary } from "../shared/api/types";

export function anAggregate(overrides: Partial<Aggregate> = {}): Aggregate {
  return {
    value: 10,
    unit: "sessions",
    available: true,
    partial: false,
    covered: 10,
    total: 10,
    coverage: 1,
    ...overrides,
  };
}

export function anIndicator(
  key: string,
  overrides: { aggregate?: Partial<Aggregate>; indicator?: Partial<Indicator> } = {},
): Indicator {
  return {
    definition: {
      key,
      label: `Libellé de ${key}`,
      unit: "sessions",
      computation: `Calcul de ${key}.`,
      scope: "Tout le périmètre filtré.",
      missing_values: "Les enregistrements sans mesure sont exclus.",
      comparability: "comparable",
    },
    aggregate: anAggregate(overrides.aggregate),
    sources: ["tracelab-claude"],
    mixes_incomparable_sources: false,
    ...overrides.indicator,
  };
}

/** Une synthèse non vide, avec les deux dénombrements attendus par le dashboard. */
export function aKpiSummary(extra: Indicator[] = []): KpiSummary {
  return {
    indicators: [
      anIndicator("sessions_total", { aggregate: { value: 12, unit: "sessions" } }),
      anIndicator("model_calls_total", { aggregate: { value: 340, unit: "appels" } }),
      ...extra,
    ],
  };
}

/** Ce que renvoie l'API tant qu'aucune trace n'a été importée. */
export function anEmptyKpiSummary(): KpiSummary {
  return {
    indicators: [
      anIndicator("sessions_total", {
        aggregate: { value: 0, unit: "sessions", covered: 0, total: 0, coverage: null },
      }),
      anIndicator("model_calls_total", {
        aggregate: { value: 0, unit: "appels", covered: 0, total: 0, coverage: null },
      }),
      anIndicator("input_tokens_total", {
        aggregate: {
          value: null,
          unit: "tokens",
          available: false,
          covered: 0,
          total: 0,
          coverage: null,
        },
      }),
    ],
  };
}
