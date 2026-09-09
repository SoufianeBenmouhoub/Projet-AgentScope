import { apiGet, apiPostForm } from "./client";
import type {
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

export function uploadImportFile(file: File, sourceName?: string): Promise<ImportRecordResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (sourceName?.trim()) {
    formData.append("source_name", sourceName.trim());
  }

  return apiPostForm<ImportRecordResponse>("/api/v1/imports", formData);
}
