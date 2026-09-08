/**
 * Construction de l'option ECharts de la courbe d'activité.
 *
 * Séparée du composant pour être testable sans DOM ni canvas.
 */

import type { ActivitySeries } from "../../../shared/api/types";
import { baseOption, categoryAxis, valueAxis, type ChartTheme } from "./theme";

const DAY = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" });

/** Au-delà de ce nombre de points, les marqueurs se chevauchent et deviennent du bruit. */
const MAX_POINTS_WITH_MARKERS = 31;

export function formatDay(isoDay: string): string {
  return DAY.format(new Date(`${isoDay}T00:00:00`));
}

export function buildActivityOption(series: ActivitySeries, theme: ChartTheme) {
  const days = series.points.map((point) => formatDay(point.day));
  const showSymbol = series.points.length <= MAX_POINTS_WITH_MARKERS;

  const line = (name: string, values: number[], color: string) => ({
    name,
    type: "line" as const,
    data: values,
    color,
    showSymbol,
    symbolSize: 8,
    lineStyle: { width: 2 },
    itemStyle: { color, borderColor: theme.surface, borderWidth: 2 },
    emphasis: { focus: "series" as const },
  });

  return {
    ...baseOption(theme),
    tooltip: {
      ...baseOption(theme).tooltip,
      trigger: "axis" as const,
      axisPointer: { type: "line" as const, lineStyle: { color: theme.axis } },
    },
    xAxis: { ...categoryAxis(theme), data: days },
    yAxis: valueAxis(theme),
    series: [
      line(
        "Sessions",
        series.points.map((point) => point.sessions),
        theme.series[0],
      ),
      line(
        "Appels au modèle",
        series.points.map((point) => point.model_calls),
        theme.series[1],
      ),
      line(
        "Appels d'outils",
        series.points.map((point) => point.tool_calls),
        theme.series[2],
      ),
    ],
  };
}

/**
 * Ce que la courbe ne peut pas montrer.
 *
 * Un enregistrement sans horodatage n'appartient à aucune journée. Le retirer en silence
 * ferait croire au lecteur que la courbe couvre tout le périmètre.
 */
export function undatedNote(series: ActivitySeries): string | null {
  if (!series.has_undated_records) {
    return null;
  }

  const parts = [
    series.undated_sessions && `${series.undated_sessions} session(s)`,
    series.undated_model_calls && `${series.undated_model_calls} appel(s) au modèle`,
    series.undated_tool_calls && `${series.undated_tool_calls} appel(s) d'outil`,
  ].filter(Boolean);

  return `Absent de cette courbe, faute d'horodatage : ${parts.join(", ")}.`;
}
