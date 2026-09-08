/**
 * Le périmètre consulté, partagé par tous les écrans du dashboard.
 *
 * Un seul objet de filtres alimente les indicateurs et les visualisations : c'est ce qui
 * garantit qu'un chiffre et un graphique affichés côte à côte parlent du même périmètre.
 */

export interface TraceFilters {
  sources: string[];
  agents: string[];
  models: string[];
  since: string | null;
  until: string | null;
}

export const NO_FILTERS: TraceFilters = {
  sources: [],
  agents: [],
  models: [],
  since: null,
  until: null,
};

/** Un filtre vide signifie « tout » : c'est l'état d'ouverture du dashboard. */
export function isUnfiltered(filters: TraceFilters): boolean {
  return (
    filters.sources.length === 0 &&
    filters.agents.length === 0 &&
    filters.models.length === 0 &&
    filters.since === null &&
    filters.until === null
  );
}

/**
 * Traduit les filtres en paramètres de requête.
 *
 * Les valeurs multiples sont répétées (`?source=a&source=b`), ce qu'attend l'API. Les
 * listes sont triées pour que deux périmètres identiques produisent la même chaîne, et
 * donc la même clé de cache.
 */
export function toSearchParams(filters: TraceFilters): URLSearchParams {
  const params = new URLSearchParams();

  for (const source of [...filters.sources].sort()) params.append("source", source);
  for (const agent of [...filters.agents].sort()) params.append("agent", agent);
  for (const model of [...filters.models].sort()) params.append("model", model);

  if (filters.since) params.set("since", filters.since);
  if (filters.until) params.set("until", filters.until);

  return params;
}

export function withPath(path: string, filters: TraceFilters): string {
  const query = toSearchParams(filters).toString();
  return query ? `${path}?${query}` : path;
}

/** Ajoute ou retire une valeur d'une liste de filtre, sans muter l'original. */
export function toggle(values: string[], value: string): string[] {
  return values.includes(value)
    ? values.filter((candidate) => candidate !== value)
    : [...values, value];
}
