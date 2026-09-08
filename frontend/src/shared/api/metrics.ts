import { apiGet } from "./client";
import type {
  ActivitySeriesResponse,
  IndicatorCatalogResponse,
  KpiSummaryResponse,
  ToolBreakdownResponse,
  TraceFilters,
} from "./types";

export function fetchKpiSummary(filters?: TraceFilters): Promise<KpiSummaryResponse> {
  return apiGet<KpiSummaryResponse>("/api/v1/metrics/summary", filters);
}

export function fetchToolBreakdown(filters?: TraceFilters): Promise<ToolBreakdownResponse> {
  return apiGet<ToolBreakdownResponse>("/api/v1/metrics/tools", filters);
}

export function fetchActivitySeries(filters?: TraceFilters): Promise<ActivitySeriesResponse> {
  return apiGet<ActivitySeriesResponse>("/api/v1/metrics/activity", filters);
}

export function fetchIndicatorDefinitions(): Promise<IndicatorCatalogResponse> {
  return apiGet<IndicatorCatalogResponse>("/api/v1/metrics/definitions");
}
