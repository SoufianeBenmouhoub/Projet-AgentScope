import { vi } from "vitest";

/**
 * Simule les réponses de l'API pour les tests d'écran.
 *
 * Chaque route est reconnue par un fragment d'URL. Une requête sans réponse simulée échoue
 * bruyamment : c'est délibéré — un écran qui appelle une route à laquelle le test n'a pas
 * pensé doit le faire savoir, pas recevoir silencieusement la mauvaise réponse.
 *
 * Le mock est retourné pour que les tests puissent inspecter les URL appelées, et donc
 * vérifier que les filtres actifs sont bien transmis.
 */
export interface StubbedRoute {
  match: string;
  body: unknown;
  ok?: boolean;
  /** Restreint la route à un verbe. Utile quand lire et écrire partagent la même URL. */
  method?: string;
}

export function stubFetch(routes: StubbedRoute[]) {
  const mock = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const route = routes.find(
      (candidate) =>
        url.includes(candidate.match) && (!candidate.method || candidate.method === method),
    );

    if (!route) {
      throw new Error(`Aucune réponse simulée pour ${method} ${url}`);
    }

    return { ok: route.ok ?? true, json: async () => route.body };
  });

  vi.stubGlobal("fetch", mock);
  return mock;
}

/** Les URL appelées, dans l'ordre. */
export function calledUrls(mock: ReturnType<typeof stubFetch>): string[] {
  return mock.mock.calls.map((call) => String(call[0]));
}
