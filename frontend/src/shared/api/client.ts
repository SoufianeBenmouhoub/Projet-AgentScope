/**
 * Client HTTP de l'application.
 *
 * Tous les appels à l'API passent par ici : un seul endroit connaît l'URL de base et le
 * traitement des erreurs.
 */

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

/**
 * La construction des paramètres de filtre vit dans `features/dashboard/filters.ts`, avec
 * le type qui les décrit. Le client HTTP n'a pas à connaître le vocabulaire du dashboard :
 * il reçoit un chemin déjà formé.
 */
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

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

/**
 * Une suppression, dont la réponse n'a pas de corps (204).
 *
 * Tenter de lire un JSON là où le serveur n'en envoie pas ferait échouer une suppression
 * pourtant réussie.
 */
export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: "DELETE" });

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorMessage(response, path, "DELETE"));
  }
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
