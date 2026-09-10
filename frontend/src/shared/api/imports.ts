import { apiGet, apiPostForm } from "./client";
import type {
  FieldMappingValues,
  ImportDetailResponse,
  ImportListResponse,
  ImportPreviewResponse,
  ImportRecordResponse,
} from "./types";

export function fetchImportHistory(): Promise<ImportListResponse> {
  return apiGet<ImportListResponse>("/api/v1/imports");
}

export function fetchImportDetail(importId: string): Promise<ImportDetailResponse> {
  return apiGet<ImportDetailResponse>(`/api/v1/imports/${encodeURIComponent(importId)}`);
}

export function previewImportFile(file: File, sourceName?: string): Promise<ImportPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (sourceName?.trim()) {
    formData.append("source_name", sourceName.trim());
  }

  return apiPostForm<ImportPreviewResponse>("/api/v1/imports/preview", formData);
}

/**
 * Lance l'import.
 *
 * Le mapping est transmis **tel que l'utilisateur l'a validé**. Omis, le serveur retombe sur
 * un préréglage ou sur une correspondance à l'identique — utile pour un fichier qui utilise
 * déjà les noms du modèle commun, jamais un substitut à la vérification.
 */
export function uploadImportFile(
  file: File,
  sourceName?: string,
  mapping?: FieldMappingValues | null,
): Promise<ImportRecordResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (sourceName?.trim()) {
    formData.append("source_name", sourceName.trim());
  }
  if (mapping) {
    formData.append("mapping", JSON.stringify(mapping));
  }

  return apiPostForm<ImportRecordResponse>("/api/v1/imports", formData);
}
