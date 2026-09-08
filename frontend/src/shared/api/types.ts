/**
 * Types des réponses de l'API.
 *
 * Écrits à la main tant que le back bouge. Dès qu'il se stabilise :
 *     npm run types:api
 */

export interface SystemStatus {
  version: string;
  database: "ok" | "unavailable";
  operational: boolean;
}

export interface AggregateResponse {
  value: number | null;
  unit: string;
  available: boolean;
  partial: boolean;
  covered: number;
  total: number;
  coverage: number | null;
}

export interface IndicatorDefinitionResponse {
  key: string;
  label: string;
  unit: string;
  computation: string;
  scope: string;
  missing_values: string;
  comparability: "comparable" | "source_specific";
}

export interface IndicatorResponse {
  definition: IndicatorDefinitionResponse;
  aggregate: AggregateResponse;
  sources: string[];
  mixes_incomparable_sources: boolean;
}

export interface KpiSummaryResponse {
  indicators: IndicatorResponse[];
}

export interface IndicatorCatalogResponse {
  definitions: IndicatorDefinitionResponse[];
}

export interface ToolUsageResponse {
  tool_name: string;
  calls: AggregateResponse;
  share: AggregateResponse;
  error_rate: AggregateResponse;
  median_latency: AggregateResponse;
  session_ids: string[];
}

export interface ToolBreakdownResponse {
  usages: ToolUsageResponse[];
  tool_calls_total: number;
  distinct_tools: number;
}

export interface ActivityPointResponse {
  day: string;
  sessions: number;
  model_calls: number;
  tool_calls: number;
  session_ids: string[];
}

export interface ActivitySeriesResponse {
  points: ActivityPointResponse[];
  undated_sessions: number;
  undated_model_calls: number;
  undated_tool_calls: number;
  has_undated_records: boolean;
}

export interface SessionEventResponse {
  kind: "model_call" | "tool_call" | string;
  label: string;
  occurred_at: string | null;
  input_tokens: number | null;
  is_error: boolean | null;
  latency_ms: number | null;
}

export interface SessionDetailResponse {
  session_id: string;
  source: string;
  agent: string;
  started_at: string | null;
  ended_at: string | null;
  duration: AggregateResponse;
  input_tokens: AggregateResponse;
  model_calls: number;
  tool_calls: number;
  failed_tool_calls: number;
  events: SessionEventResponse[];
}

/** Périmètre de filtrage partagé par toutes les routes du dashboard. */
export interface TraceFilters {
  sources: string[];
  agents: string[];
  models: string[];
  sessionIds: string[];
  since: string | null;
  until: string | null;
}

export const EMPTY_TRACE_FILTERS: TraceFilters = {
  sources: [],
  agents: [],
  models: [],
  sessionIds: [],
  since: null,
  until: null,
};

export type ImportStatus = "pending" | "running" | "completed" | "failed" | "duplicate";

export type ImportFormat = "jsonl" | "csv" | "parquet";

export interface ImportRejectionResponse {
  line_number: number;
  reason: string;
  raw_preview: string | null;
}

export interface ImportRecordResponse {
  id: string;
  source_name: string;
  filename: string;
  format: ImportFormat;
  imported_at: string;
  status: ImportStatus;
  records_imported: number;
  duplicates_count: number;
  rejected_count: number;
  missing_data_count: number;
}

export interface ImportListResponse {
  imports: ImportRecordResponse[];
}

export interface ImportDetailResponse extends ImportRecordResponse {
  rejections: ImportRejectionResponse[];
}

export interface ImportPreviewResponse {
  filename: string;
  format: ImportFormat;
  row_count_sample: number;
  columns: string[];
  sample_rows: Record<string, unknown>[];
}
