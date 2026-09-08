/**
 * Accès aux données du dashboard.
 *
 * Un seul endroit connaît les chemins de l'API et les clés de cache. Chaque requête est
 * indexée sur les filtres actifs : changer de périmètre change la clé, donc les chiffres
 * affichés ne peuvent pas provenir d'un périmètre différent de celui des graphiques.
 */

import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";
import type {
  ActivitySeries,
  FilterOptions,
  KpiSummary,
  ToolBreakdown,
} from "../../shared/api/types";
import { withPath, type TraceFilters } from "./filters";

export function useFilterOptions() {
  return useQuery({
    queryKey: ["metrics", "filters"],
    queryFn: () => apiGet<FilterOptions>("/api/v1/metrics/filters"),
  });
}

export function useKpiSummary(filters: TraceFilters) {
  return useQuery({
    queryKey: ["metrics", "summary", filters],
    queryFn: () => apiGet<KpiSummary>(withPath("/api/v1/metrics/summary", filters)),
  });
}

export function useToolBreakdown(filters: TraceFilters) {
  return useQuery({
    queryKey: ["metrics", "tools", filters],
    queryFn: () => apiGet<ToolBreakdown>(withPath("/api/v1/metrics/tools", filters)),
  });
}

export function useActivitySeries(filters: TraceFilters) {
  return useQuery({
    queryKey: ["metrics", "activity", filters],
    queryFn: () => apiGet<ActivitySeries>(withPath("/api/v1/metrics/activity", filters)),
  });
}
