import type { AggregateResponse } from "../../../shared/api/types";

/** Une mesure est-elle réellement disponible ? Jamais confondue avec zéro. */
export function isAggregateAvailable(aggregate: AggregateResponse): boolean {
  return aggregate.available && aggregate.value !== null;
}

/** Formate une agrégation pour l'affichage. Retourne « — » si indisponible. */
export function formatAggregateValue(aggregate: AggregateResponse): string {
  if (!isAggregateAvailable(aggregate)) {
    return "—";
  }

  const value = aggregate.value as number;

  if (aggregate.unit === "%") {
    return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
  }

  if (aggregate.unit === "ms") {
    return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 0 })} ms`;
  }

  if (Number.isInteger(value)) {
    return value.toLocaleString("fr-FR");
  }

  return value.toLocaleString("fr-FR", { maximumFractionDigits: 2 });
}

/** Couverture en pourcentage lisible, ou null si non calculable. */
export function formatCoverage(aggregate: AggregateResponse): string | null {
  if (aggregate.coverage === null) {
    return null;
  }

  return `${Math.round(aggregate.coverage * 100)} %`;
}
