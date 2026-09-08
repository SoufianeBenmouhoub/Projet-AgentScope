import type { TraceFilters } from "../../../shared/api/types";
import { EMPTY_TRACE_FILTERS } from "../../../shared/api/types";

function splitList(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

/** Lit les filtres depuis les paramètres d'URL. */
export function parseFiltersFromSearchParams(params: URLSearchParams): TraceFilters {
  const listParam = (key: string): string[] => params.getAll(key);

  const sources = listParam("source");
  const agents = listParam("agent");
  const models = listParam("model");
  const sessionIds = listParam("session_id");

  const legacySource = params.get("sources");
  const legacyAgent = params.get("agents");
  const legacyModel = params.get("models");

  return {
    sources: sources.length > 0 ? sources : legacySource ? splitList(legacySource) : [],
    agents: agents.length > 0 ? agents : legacyAgent ? splitList(legacyAgent) : [],
    models: models.length > 0 ? models : legacyModel ? splitList(legacyModel) : [],
    sessionIds,
    since: params.get("since"),
    until: params.get("until"),
  };
}

/** Écrit les filtres dans les paramètres d'URL. */
export function writeFiltersToSearchParams(
  filters: TraceFilters,
  base: URLSearchParams = new URLSearchParams(),
): URLSearchParams {
  const params = new URLSearchParams(base);

  for (const key of ["source", "agent", "model", "session_id", "since", "until"] as const) {
    params.delete(key);
  }
  params.delete("sources");
  params.delete("agents");
  params.delete("models");

  for (const source of filters.sources) {
    params.append("source", source);
  }
  for (const agent of filters.agents) {
    params.append("agent", agent);
  }
  for (const model of filters.models) {
    params.append("model", model);
  }
  for (const sessionId of filters.sessionIds) {
    params.append("session_id", sessionId);
  }
  if (filters.since) {
    params.set("since", filters.since);
  }
  if (filters.until) {
    params.set("until", filters.until);
  }

  return params;
}

export function filtersAreEmpty(filters: TraceFilters): boolean {
  return (
    filters.sources.length === 0 &&
    filters.agents.length === 0 &&
    filters.models.length === 0 &&
    filters.sessionIds.length === 0 &&
    !filters.since &&
    !filters.until
  );
}

export function mergeFilters(
  current: TraceFilters,
  patch: Partial<TraceFilters>,
): TraceFilters {
  return { ...current, ...patch };
}

export { EMPTY_TRACE_FILTERS };
