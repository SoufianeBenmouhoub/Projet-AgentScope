import { apiDelete, apiGet, apiPostJson } from "./client";
import type {
  FieldMappingValues,
  MappingContract,
  MappingPreview,
  MappingProposal,
  SavedMapping,
  SavedMappingList,
} from "./types";

/** Les champs du modèle commun qu'un mapping peut renseigner, tels que le serveur les déclare. */
export function fetchMappingFields(): Promise<MappingContract> {
  return apiGet<MappingContract>("/api/v1/mapping/fields");
}

/** Demande à l'agent IA configuré une correspondance pour cet échantillon. */
export function proposeMapping(
  records: Record<string, unknown>[],
  sourceFormat: string,
): Promise<MappingProposal> {
  return apiPostJson<MappingProposal>("/api/v1/mapping/propose", {
    source_format: sourceFormat,
    records,
  });
}

/** Essaie un mapping sur l'échantillon, sans rien écrire. */
export function previewMapping(
  records: Record<string, unknown>[],
  mapping: FieldMappingValues,
): Promise<MappingPreview> {
  return apiPostJson<MappingPreview>("/api/v1/mapping/preview", { records, mapping });
}

export function fetchSavedMappings(): Promise<SavedMappingList> {
  return apiGet<SavedMappingList>("/api/v1/mappings");
}

export function saveMapping(
  name: string,
  mapping: FieldMappingValues,
  sourceName?: string,
): Promise<SavedMapping> {
  return apiPostJson<SavedMapping>("/api/v1/mappings", {
    name,
    source_name: sourceName?.trim() || null,
    mapping,
  });
}

export function deleteMapping(mappingId: string): Promise<void> {
  return apiDelete(`/api/v1/mappings/${encodeURIComponent(mappingId)}`);
}
