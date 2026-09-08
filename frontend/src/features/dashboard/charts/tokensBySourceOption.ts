/**
 * Construction de l'option ECharts des tokens par source.
 *
 * Ce graphique existe pour une raison précise : **rendre visible que toutes les sources ne
 * mesurent pas la même chose.** Les tokens de création de cache ne sont publiés que par
 * certains agents. Les additionner donnerait un total qui a l'air juste et qui est faux ;
 * les afficher côte à côte, avec un trou explicite là où la mesure n'existe pas, dit la
 * vérité.
 *
 * Les valeurs viennent d'une interrogation **par source**, jamais d'un total découpé après
 * coup : c'est la séparation demandée, appliquée à la lettre.
 */

import type { Aggregate, KpiSummary } from "../../../shared/api/types";
import { baseOption, categoryAxis, valueAxis, type ChartTheme } from "./theme";

export interface SourceTokens {
  source: string;
  inputTokens: Aggregate | null;
  cacheTokens: Aggregate | null;
}

function indicatorOf(summary: KpiSummary | undefined, key: string): Aggregate | null {
  return summary?.indicators.find((item) => item.definition.key === key)?.aggregate ?? null;
}

export function toSourceTokens(
  rows: { source: string; summary: KpiSummary | undefined }[],
): SourceTokens[] {
  return rows.map((row) => ({
    source: row.source,
    inputTokens: indicatorOf(row.summary, "input_tokens_total"),
    cacheTokens: indicatorOf(row.summary, "cache_creation_tokens"),
  }));
}

export function buildTokensBySourceOption(rows: SourceTokens[], theme: ChartTheme) {
  const bar = (name: string, values: (number | null)[], color: string) => ({
    name,
    type: "bar" as const,
    data: values,
    color,
    barMaxWidth: 28,
    barCategoryGap: "40%",
    barGap: "10%",
    itemStyle: { borderRadius: [4, 4, 0, 0] },
  });

  return {
    ...baseOption(theme),
    tooltip: { ...baseOption(theme).tooltip, trigger: "axis" as const, axisPointer: { type: "shadow" as const } },
    xAxis: { ...categoryAxis(theme), data: rows.map((row) => row.source) },
    yAxis: valueAxis(theme),
    series: [
      bar(
        "Tokens en entrée",
        rows.map((row) => row.inputTokens?.value ?? null),
        theme.series[0],
      ),
      bar(
        "Tokens de création de cache",
        rows.map((row) => row.cacheTokens?.value ?? null),
        theme.series[1],
      ),
    ],
  };
}

/**
 * Ce que l'absence de barre signifie.
 *
 * Sans cette note, un trou dans le graphique se lit comme un zéro. C'est exactement
 * l'erreur que le projet cherche à éviter.
 */
export function missingMeasureNote(rows: SourceTokens[]): string | null {
  const withoutCache = rows
    .filter((row) => row.cacheTokens !== null && row.cacheTokens.value === null)
    .map((row) => row.source);

  if (withoutCache.length === 0) {
    return null;
  }

  return `Aucune barre ne signifie « non publié », pas « zéro » : ${withoutCache.join(
    ", ",
  )} ne fournit pas les tokens de création de cache.`;
}
