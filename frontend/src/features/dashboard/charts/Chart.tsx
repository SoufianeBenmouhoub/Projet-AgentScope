/**
 * Le composant de graphique du projet.
 *
 * ECharts est importé **module par module** : seuls les types de graphique et les
 * composants réellement utilisés entrent dans le paquet livré au navigateur. Importer la
 * bibliothèque entière la faisait passer de 190 ko à 1,3 Mo pour deux formes de graphique.
 *
 * Ajouter une forme (camembert, nuage de points…) demande de l'enregistrer ici, dans
 * l'appel à `echarts.use`. C'est volontaire : ça garde le coût visible.
 */

import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import ReactEChartsCore from "echarts-for-react/lib/core";

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
]);

/** Ce qu'un clic sur une marque du graphique fait remonter. */
export interface ChartClick {
  dataIndex: number;
  seriesIndex: number;
}

interface Props {
  option: object;
  style?: React.CSSProperties;
  /** Rend le graphique cliquable : c'est le point de départ du retour vers les sessions. */
  onSelect?: (click: ChartClick) => void;
}

export function Chart({ option, style, onSelect }: Props) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={style}
      notMerge
      onEvents={
        onSelect
          ? {
              click: (params: ChartClick) =>
                onSelect({ dataIndex: params.dataIndex, seriesIndex: params.seriesIndex }),
            }
          : undefined
      }
    />
  );
}
