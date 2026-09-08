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
