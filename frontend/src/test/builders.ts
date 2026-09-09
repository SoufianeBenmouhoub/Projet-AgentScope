/**
 * Constructeurs de réponses d'API pour les tests du front.
 *
 * Ces données sont **fictives et réservées aux tests** : le dashboard livré n'affiche que
 * des données réellement importées.
 */

import type {
  ActivitySeries,
  Aggregate,
  FilterOptions,
  Indicator,
  KpiSummary,
  SessionDetail,
  SessionList,
  SessionSummary,
  ToolBreakdown,
  ToolUsage,
} from "../shared/api/types";

export function anActivitySeries(overrides: Partial<ActivitySeries> = {}): ActivitySeries {
  return {
    points: [
      { day: "2026-09-01", sessions: 2, model_calls: 10, tool_calls: 5, session_ids: ["s1"] },
      { day: "2026-09-02", sessions: 1, model_calls: 4, tool_calls: 2, session_ids: ["s2"] },
    ],
    undated_sessions: 0,
    undated_model_calls: 0,
    undated_tool_calls: 0,
    has_undated_records: false,
    ...overrides,
  };
}

export function aToolUsage(name: string, calls = 5): ToolUsage {
  return {
    tool_name: name,
    calls: anAggregate({ value: calls, unit: "appels" }),
    share: anAggregate({ value: 50, unit: "%" }),
    error_rate: anAggregate({ value: 0, unit: "%" }),
    median_latency: anAggregate({ value: 120, unit: "ms" }),
    session_ids: ["s1"],
  };
}

export function aToolBreakdown(overrides: Partial<ToolBreakdown> = {}): ToolBreakdown {
  return {
    usages: [aToolUsage("read_file", 6), aToolUsage("bash", 4)],
    tool_calls_total: 10,
    distinct_tools: 2,
    ...overrides,
  };
}

export function aSessionSummary(sessionId = "s1"): SessionSummary {
  return {
    session_id: sessionId,
    source: "tracelab-claude",
    agent: "claude-code",
    started_at: "2026-09-01T10:00:00",
    ended_at: "2026-09-01T10:30:00",
    duration: anAggregate({ value: 1800, unit: "s" }),
    model_calls: 4,
    tool_calls: 2,
    input_tokens: anAggregate({ value: 900, unit: "tokens" }),
  };
}

export function aSessionList(overrides: Partial<SessionList> = {}): SessionList {
  return {
    sessions: [aSessionSummary("s1")],
    total: 1,
    truncated: false,
    ...overrides,
  };
}

export function aSessionDetail(overrides: Partial<SessionDetail> = {}): SessionDetail {
  return {
    session_id: "s1",
    source: "tracelab-claude",
    agent: "claude-code",
    started_at: "2026-09-01T10:00:00",
    ended_at: "2026-09-01T10:30:00",
    duration: anAggregate({ value: 1800, unit: "s" }),
    input_tokens: anAggregate({ value: 900, unit: "tokens" }),
    model_calls: 1,
    tool_calls: 1,
    failed_tool_calls: 0,
    events: [
      {
        kind: "model_call",
        label: "claude-opus-5",
        occurred_at: "2026-09-01T10:05:00",
        input_tokens: 900,
        is_error: null,
        latency_ms: null,
      },
      {
        kind: "tool_call",
        label: "bash",
        occurred_at: null,
        input_tokens: null,
        is_error: null,
        latency_ms: null,
      },
    ],
    ...overrides,
  };
}

export function someFilterOptions(overrides: Partial<FilterOptions> = {}): FilterOptions {
  return {
    sources: ["tracelab-claude", "tracelab-codex"],
    agents: ["claude-code", "codex"],
    models: ["claude-opus-5"],
    first_day: "2026-09-01",
    last_day: "2026-09-08",
    is_empty: false,
    ...overrides,
  };
}

/** Ce que renvoie l'API tant qu'aucune trace n'a été importée. */
export function noFilterOptions(): FilterOptions {
  return {
    sources: [],
    agents: [],
    models: [],
    first_day: null,
    last_day: null,
    is_empty: true,
  };
}

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
  overrides: {
    aggregate?: Partial<Aggregate>;
    indicator?: Partial<Indicator>;
    kind?: "count" | "measure";
  } = {},
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
      kind: overrides.kind ?? "measure",
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
