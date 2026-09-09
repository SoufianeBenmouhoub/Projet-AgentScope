/**
 * Ce que les données ne disent pas.
 *
 * L'énoncé demande que « le dashboard rende visible la qualité des données importées ».
 * Concrètement : un chiffre partiel doit dire sur quelle part du périmètre il porte, un
 * indicateur absent doit dire pourquoi, et ce qu'une visualisation ne peut pas montrer doit
 * être compté ailleurs.
 *
 * Tout se déduit de ce que l'API expose déjà. Aucune donnée n'est estimée ici.
 */

import type { ActivitySeries, Indicator, KpiSummary } from "../../../shared/api/types";

export interface MeasureCoverage {
  key: string;
  label: string;
  covered: number;
  total: number;
  /** Part du périmètre qui renseigne la mesure, de 0 à 1. `null` si le périmètre est vide. */
  ratio: number | null;
  available: boolean;
}

export interface SourceCoverage {
  source: string;
  measures: MeasureCoverage[];
}

export interface UnavailableIndicator {
  label: string;
  reason: string;
}

/** Un dénombrement est complet par construction : sa couverture n'apprend rien. */
function isMeasure(indicator: Indicator): boolean {
  return indicator.definition.kind === "measure";
}

/**
 * La complétude de chaque mesure, source par source.
 *
 * C'est le tableau qui rend visible d'un coup d'œil qu'une source ne publie pas ce qu'une
 * autre publie — et donc pourquoi certains chiffres ne sont pas comparables.
 */
export function toCoverageBySource(
  rows: { source: string; summary: KpiSummary | undefined }[],
): SourceCoverage[] {
  return rows
    .filter((row) => row.summary !== undefined)
    .map((row) => ({
      source: row.source,
      measures: row.summary!.indicators.filter(isMeasure).map((indicator) => ({
        key: indicator.definition.key,
        label: indicator.definition.label,
        covered: indicator.aggregate.covered,
        total: indicator.aggregate.total,
        ratio: indicator.aggregate.coverage,
        available: indicator.aggregate.available,
      })),
    }));
}

/**
 * Les indicateurs qu'on ne peut pas afficher, et la raison exacte.
 *
 * Un chiffre absent sans explication ressemble à une panne. Avec sa raison, il devient une
 * information sur les données.
 */
export function unavailableIndicators(summary: KpiSummary): UnavailableIndicator[] {
  return summary.indicators
    .filter((indicator) => !indicator.aggregate.available)
    .map((indicator) => ({
      label: indicator.definition.label,
      reason: indicator.definition.missing_values,
    }));
}

/** Les indicateurs affichés qui ne portent que sur une partie du périmètre. */
export function partialIndicators(summary: KpiSummary): UnavailableIndicator[] {
  return summary.indicators
    .filter((indicator) => indicator.aggregate.partial)
    .map((indicator) => ({
      label: indicator.definition.label,
      reason: `Calculé sur ${indicator.aggregate.covered} des ${indicator.aggregate.total} enregistrements du périmètre.`,
    }));
}

/** Ce qui est exclu des vues temporelles faute d'horodatage. */
export function undatedRecords(series: ActivitySeries): { label: string; count: number }[] {
  return [
    { label: "Sessions", count: series.undated_sessions },
    { label: "Appels au modèle", count: series.undated_model_calls },
    { label: "Appels d'outils", count: series.undated_tool_calls },
  ].filter((entry) => entry.count > 0);
}
