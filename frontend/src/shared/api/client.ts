/**
 * Client HTTP de l'application.
 *
 * Tous les appels à l'API passent par ici : un seul endroit connaît l'URL de base, le
 * traitement des erreurs et, plus tard, l'authentification.
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

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new ApiError(response.status, `GET ${path} a répondu ${response.status}.`);
  }

  return (await response.json()) as T;
}
