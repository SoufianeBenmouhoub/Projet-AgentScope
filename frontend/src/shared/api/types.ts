/**
 * Types des réponses de l'API.
 *
 * Ils ne sont plus écrits à la main : ils sont dérivés du document OpenAPI publié par
 * FastAPI, régénéré par
 *
 *     npm run types:api        (le back doit tourner)
 *
 * L'intérêt n'est pas d'économiser de la frappe. C'est qu'une divergence entre le contrat
 * exposé par le back et ce que le front consomme casse le build, au lieu de produire un
 * graphe silencieusement faux.
 */

import type { components } from "./schema";

type Schemas = components["schemas"];

export type SystemStatus = Schemas["SystemStatusResponse"];

/**
 * Résultat d'une agrégation, avec son périmètre réel.
 *
 * `value` à `null` signifie **non disponible**, jamais zéro. `covered` et `total` disent
 * sur combien d'enregistrements le chiffre porte réellement.
 */
export type Aggregate = Schemas["AggregateResponse"];

export type IndicatorDefinition = Schemas["IndicatorDefinitionResponse"];
export type Indicator = Schemas["IndicatorResponse"];
export type KpiSummary = Schemas["KpiSummaryResponse"];
export type IndicatorCatalog = Schemas["IndicatorCatalogResponse"];

export type FilterOptions = Schemas["FilterOptionsResponse"];

export type ToolUsage = Schemas["ToolUsageResponse"];
export type ToolBreakdown = Schemas["ToolBreakdownResponse"];

export type ActivityPoint = Schemas["ActivityPointResponse"];
export type ActivitySeries = Schemas["ActivitySeriesResponse"];

export type SessionEvent = Schemas["SessionEventResponse"];
export type SessionDetail = Schemas["SessionDetailResponse"];
export type SessionSummary = Schemas["SessionSummaryResponse"];
export type SessionList = Schemas["SessionListResponse"];

/* -------------------------------------------------------------------------------------
 * Import — types provisoires
 *
 * Ceux-ci sont écrits à la main, contrairement à tous les précédents. Ce n'est pas un
 * oubli : **l'API d'import n'existe pas encore côté serveur**, il n'y a donc rien à
 * générer. Ils décrivent le contrat que l'écran d'import attend du lot 3.
 *
 * Dès que les routes `/api/v1/imports` existeront, ce bloc disparaît au profit de
 * `npm run types:api`. Tant qu'il est là, il signale une API attendue mais absente — et
 * l'écran d'import ne peut pas fonctionner de bout en bout.
 * ----------------------------------------------------------------------------------- */

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
