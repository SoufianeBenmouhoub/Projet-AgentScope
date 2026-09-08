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

interface Props {
  option: object;
  style?: React.CSSProperties;
}

export function Chart({ option, style }: Props) {
  return <ReactEChartsCore echarts={echarts} option={option} style={style} notMerge />;
}
