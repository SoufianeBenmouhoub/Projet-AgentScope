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

/* Import — dérivés du schéma OpenAPI comme le reste, depuis que les routes existent. */

export type ImportPreviewResponse = Schemas["ImportPreviewResponse"];
export type ImportRecordResponse = Schemas["ImportRecordResponse"];
export type ImportListResponse = Schemas["ImportListResponse"];
export type ImportDetailResponse = Schemas["ImportDetailResponse"];
export type ImportRejectionResponse = Schemas["ImportRejectionResponse"];

/* Mapping — le contrat visé, la proposition de l'IA, l'essai à blanc, la bibliothèque. */

export type TargetField = Schemas["TargetFieldResponse"];
export type MappingContract = Schemas["MappingContractResponse"];
export type FieldMapping = Schemas["FieldMappingResponse"];
export type MappingProposal = Schemas["MappingProposalResponse"];
export type FieldOutcome = Schemas["FieldOutcomeResponse"];
export type MappingPreview = Schemas["MappingPreviewResponse"];
export type SavedMapping = Schemas["SavedMappingResponse"];
export type SavedMappingList = Schemas["SavedMappingListResponse"];

/**
 * Un mapping tel qu'il circule : champ du modèle commun → chemin dans l'enregistrement
 * source, ou `null` quand la source ne publie rien pour ce champ.
 */
export type FieldMappingValues = Record<string, string | null>;

/**
 * Les statuts et formats restent des unions écrites à la main : le serveur les expose en
 * texte libre, et les figer ici documente ce que l'interface sait afficher.
 */
export type ImportStatus = "pending" | "running" | "completed" | "failed" | "duplicate";
export type ImportFormat = "jsonl" | "csv" | "parquet";
