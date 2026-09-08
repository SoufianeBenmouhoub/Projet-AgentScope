/**
 * Accès aux données du dashboard.
 *
 * Un seul endroit connaît les chemins de l'API et les clés de cache. Les composants ne
 * font qu'appeler ces hooks.
 */

import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";
import type { ActivitySeries, KpiSummary, ToolBreakdown } from "../../shared/api/types";

export function useKpiSummary() {
  return useQuery({
    queryKey: ["metrics", "summary"],
    queryFn: () => apiGet<KpiSummary>("/api/v1/metrics/summary"),
  });
}

export function useToolBreakdown() {
  return useQuery({
    queryKey: ["metrics", "tools"],
    queryFn: () => apiGet<ToolBreakdown>("/api/v1/metrics/tools"),
  });
}

export function useActivitySeries() {
  return useQuery({
    queryKey: ["metrics", "activity"],
    queryFn: () => apiGet<ActivitySeries>("/api/v1/metrics/activity"),
  });
}
