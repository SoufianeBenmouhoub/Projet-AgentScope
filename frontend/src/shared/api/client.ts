/**
 * Client HTTP de l'application.
 *
 * Tous les appels à l'API passent par ici : un seul endroit connaît l'URL de base et le
 * traitement des erreurs.
 */

import type { TraceFilters } from "./types";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Traduit les filtres en paramètres de requête répétables. */
export function buildQueryString(filters?: Partial<TraceFilters>): string {
  if (!filters) {
    return "";
  }

  const params = new URLSearchParams();

  for (const source of filters.sources ?? []) {
    if (source.trim()) {
      params.append("source", source.trim());
    }
  }
  for (const agent of filters.agents ?? []) {
    if (agent.trim()) {
      params.append("agent", agent.trim());
    }
  }
  for (const model of filters.models ?? []) {
    if (model.trim()) {
      params.append("model", model.trim());
    }
  }
  for (const sessionId of filters.sessionIds ?? []) {
    if (sessionId.trim()) {
      params.append("session_id", sessionId.trim());
    }
  }
  if (filters.since) {
    params.set("since", filters.since);
  }
  if (filters.until) {
    params.set("until", filters.until);
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function apiGet<T>(path: string, filters?: Partial<TraceFilters>): Promise<T> {
  const query = buildQueryString(filters);
  const url = `${API_BASE_URL}${path}${query}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new ApiError(response.status, `GET ${path} a répondu ${response.status}.`);
  }

  return (await response.json()) as T;
}

async function readErrorMessage(response: Response, path: string, method: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg;
    }
  } catch {
    // Corps non JSON — message générique ci-dessous.
  }

  return `${method} ${path} a répondu ${response.status}.`;
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await readErrorMessage(response, path, "POST");
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const message = await readErrorMessage(response, path, "POST");
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}
