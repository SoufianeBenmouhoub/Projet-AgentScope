import type { ActivitySeries } from "../../../shared/api/types";
import { buildActivityOption, formatDay, undatedNote } from "./activityOption";
import { Chart } from "./Chart";
import { ChartCard } from "./ChartCard";
import { useChartTheme } from "./theme";

export function ActivityChart({
  series,
  refreshing,
  onSelect,
}: {
  series: ActivitySeries;
  refreshing?: boolean;
  /** Un clic sur une journée fait remonter ses sessions. */
  onSelect?: (sessionIds: string[], origin: string) => void;
}) {
  const theme = useChartTheme();
  const note = undatedNote(series);

  return (
    <ChartCard
      title="Activité dans le temps"
      note={note}
      refreshing={refreshing}
      table={
        <table>
          <caption className="sr-only">Activité par journée</caption>
          <thead>
            <tr>
              <th scope="col">Journée</th>
              <th scope="col">Sessions</th>
              <th scope="col">Appels au modèle</th>
              <th scope="col">Appels d'outils</th>
            </tr>
          </thead>
          <tbody>
            {series.points.map((point) => (
              <tr key={point.day}>
                <th scope="row">{formatDay(point.day)}</th>
                <td>{point.sessions}</td>
                <td>{point.model_calls}</td>
                <td>{point.tool_calls}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {series.points.length === 0 ? (
        <p className="chart__empty">Aucun enregistrement horodaté dans ce périmètre.</p>
      ) : (
        <Chart
          option={buildActivityOption(series, theme)}
          style={{ height: 260 }}
          onSelect={
            onSelect &&
            (({ dataIndex }) => {
              const point = series.points[dataIndex];
              if (point) {
                onSelect(point.session_ids, `journée du ${formatDay(point.day)}`);
              }
            })
          }
        />
      )}
    </ChartCard>
  );
}
