/**
 * Types des réponses de l'API.
 *
 * Ils sont écrits à la main tant que le back bouge beaucoup. Dès qu'il se stabilise, on
 * les génère depuis le document OpenAPI produit par FastAPI :
 *
 *     npm run types:api
 *
 * L'intérêt n'est pas d'économiser de la frappe : c'est qu'une divergence entre le contrat
 * exposé par le back et ce que le front consomme casse le build, au lieu de produire un
 * graphe silencieusement faux.
 */

export interface SystemStatus {
  version: string;
  database: "ok" | "unavailable";
  operational: boolean;
}
