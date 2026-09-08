/**
 * Jetons de couleur des graphiques.
 *
 * Les trois couleurs de série sont prises **dans un ordre fixe** : une série garde sa
 * couleur quels que soient les filtres actifs. Un lecteur qui a appris « les sessions sont
 * bleues » ne doit pas voir la couleur changer parce qu'il a filtré.
 *
 * Les deux jeux ont été validés séparément contre leur surface respective — le mode sombre
 * n'est pas une inversion automatique du mode clair. Seule réserve connue : en mode clair,
 * l'aqua passe sous 3:1 de contraste avec la surface, ce qui impose la vue tableau
 * proposée sous chaque graphique.
 */

import { useEffect, useState } from "react";

export interface ChartTheme {
  series: [string, string, string];
  surface: string;
  textPrimary: string;
  textSecondary: string;
  muted: string;
  gridline: string;
  axis: string;
}

const LIGHT: ChartTheme = {
  series: ["#2a78d6", "#eb6834", "#1baf7a"],
  surface: "#fcfcfb",
  textPrimary: "#0b0b0b",
  textSecondary: "#52514e",
  muted: "#898781",
  gridline: "#e1e0d9",
  axis: "#c3c2b7",
};

const DARK: ChartTheme = {
  series: ["#3987e5", "#d95926", "#199e70"],
  surface: "#1a1a19",
  textPrimary: "#ffffff",
  textSecondary: "#c3c2b7",
  muted: "#898781",
  gridline: "#2c2c2a",
  axis: "#383835",
};

const DARK_QUERY = "(prefers-color-scheme: dark)";

function prefersDark(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia(DARK_QUERY).matches;
}

export function useChartTheme(): ChartTheme {
  const [dark, setDark] = useState(prefersDark);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }

    const media = window.matchMedia(DARK_QUERY);
    const listener = (event: MediaQueryListEvent) => setDark(event.matches);

    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, []);

  return dark ? DARK : LIGHT;
}

/** Chrome commun à tous les graphiques : grille et axes discrets, texte en encre. */
export function baseOption(theme: ChartTheme) {
  return {
    backgroundColor: "transparent",
    textStyle: {
      fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
      color: theme.textSecondary,
    },
    grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: theme.surface,
      borderColor: theme.axis,
      borderWidth: 1,
      textStyle: { color: theme.textPrimary, fontSize: 12 },
    },
    legend: {
      top: 0,
      left: 0,
      icon: "roundRect",
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: theme.textSecondary, fontSize: 12 },
    },
  };
}

export function categoryAxis(theme: ChartTheme) {
  return {
    type: "category" as const,
    axisLine: { lineStyle: { color: theme.axis } },
    axisTick: { show: false },
    axisLabel: { color: theme.muted, fontSize: 11 },
  };
}

export function valueAxis(theme: ChartTheme) {
  return {
    type: "value" as const,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: theme.muted, fontSize: 11 },
    splitLine: { lineStyle: { color: theme.gridline, width: 1, type: "solid" as const } },
  };
}
