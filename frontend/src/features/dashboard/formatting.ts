/**
 * Mise en forme des agrégats.
 *
 * **La règle qui gouverne ce module : une valeur indisponible s'affiche « n/a ».**
 * Jamais « 0 ». C'est le dernier maillon d'une chaîne qui commence dans le schéma SQL, et
 * c'est celui où l'erreur serait la plus visible pour l'utilisateur — et la plus fausse.
 */

import type { Aggregate } from "../../shared/api/types";

export const UNAVAILABLE = "n/a";

const NUMBER = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
const DECIMAL = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/** La valeur mise en forme, unité comprise, ou « n/a » si elle n'est pas disponible. */
export function formatAggregate(aggregate: Aggregate): string {
  if (aggregate.value === null) {
    return UNAVAILABLE;
  }

  switch (aggregate.unit) {
    case "%":
      return `${DECIMAL.format(aggregate.value)} %`;
    case "ms":
      return `${NUMBER.format(aggregate.value)} ms`;
    case "s":
      return `${NUMBER.format(aggregate.value)} s`;
    default:
      return `${NUMBER.format(aggregate.value)} ${aggregate.unit}`;
  }
}

/**
 * Le message qui explique pourquoi un chiffre est absent ou incomplet.
 *
 * `null` quand il n'y a rien à signaler — la valeur porte sur tout le périmètre.
 */
export function coverageNote(aggregate: Aggregate): string | null {
  if (aggregate.value === null) {
    return aggregate.total === 0
      ? "Aucun enregistrement dans le périmètre."
      : `Aucun des ${NUMBER.format(aggregate.total)} enregistrements du périmètre ne renseigne cette mesure.`;
  }

  if (aggregate.covered < aggregate.total) {
    const share = DECIMAL.format((aggregate.coverage ?? 0) * 100);
    return `Calculé sur ${NUMBER.format(aggregate.covered)} des ${NUMBER.format(
      aggregate.total,
    )} enregistrements du périmètre (${share} %).`;
  }

  return null;
}
