/**
 * Construction de l'option ECharts de la répartition des outils.
 *
 * Une seule série, donc une seule couleur : la longueur de la barre porte déjà la
 * grandeur, teinter chaque barre différemment doublerait l'encodage sans rien apprendre.
 */

import type { ToolBreakdown, ToolUsage } from "../../../shared/api/types";
import { baseOption, categoryAxis, valueAxis, type ChartTheme } from "./theme";

/** Au-delà, les barres deviennent illisibles : le reste est replié dans « Autres ». */
export const MAX_TOOLS = 10;

export interface ToolBar {
  name: string;
  calls: number;
  usage: ToolUsage | null;
  /** Les sessions où cet outil apparaît : le point de départ du retour aux enregistrements. */
  sessionIds: string[];
}

/**
 * Les outils à représenter, du plus utilisé au moins utilisé.
 *
 * La queue est repliée dans une entrée « Autres » plutôt que tronquée : le total reste
 * juste, et le lecteur voit qu'il manque quelque chose.
 */
export function toBars(breakdown: ToolBreakdown): ToolBar[] {
  const usages = breakdown.usages;

  const toBar = (usage: ToolUsage): ToolBar => ({
    name: usage.tool_name,
    calls: usage.calls.value ?? 0,
    usage,
    sessionIds: usage.session_ids,
  });

  if (usages.length <= MAX_TOOLS) {
    return usages.map(toBar);
  }

  const head = usages.slice(0, MAX_TOOLS - 1);
  const tail = usages.slice(MAX_TOOLS - 1);

  return [
    ...head.map(toBar),
    {
      name: `Autres (${tail.length} outils)`,
      calls: tail.reduce((total, usage) => total + (usage.calls.value ?? 0), 0),
      usage: null,
      // La barre repliée reste cliquable : elle mène aux sessions de tous les outils
      // qu'elle regroupe.
      sessionIds: [...new Set(tail.flatMap((usage) => usage.session_ids))].sort(),
    },
  ];
}

export function buildToolBreakdownOption(bars: ToolBar[], theme: ChartTheme) {
  // ECharts empile l'axe des catégories du bas vers le haut : on inverse pour que le plus
  // utilisé apparaisse en haut.
  const ordered = [...bars].reverse();

  return {
    ...baseOption(theme),
    grid: { left: 8, right: 48, top: 8, bottom: 8, containLabel: true },
    tooltip: { ...baseOption(theme).tooltip, trigger: "item" as const },
    legend: { show: false },
    xAxis: valueAxis(theme),
    yAxis: { ...categoryAxis(theme), data: ordered.map((bar) => bar.name) },
    series: [
      {
        type: "bar" as const,
        data: ordered.map((bar) => bar.calls),
        color: theme.series[0],
        barMaxWidth: 18,
        barCategoryGap: "35%",
        itemStyle: { borderRadius: [0, 4, 4, 0] },
        label: {
          show: true,
          position: "right" as const,
          color: theme.textSecondary,
          fontSize: 11,
        },
      },
    ],
  };
}
