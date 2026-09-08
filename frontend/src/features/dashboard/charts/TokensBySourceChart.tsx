import { formatAggregate, UNAVAILABLE } from "../formatting";
import { Chart } from "./Chart";
import { ChartCard } from "./ChartCard";
import { useChartTheme } from "./theme";
import {
  buildTokensBySourceOption,
  missingMeasureNote,
  type SourceTokens,
} from "./tokensBySourceOption";

export function TokensBySourceChart({
  rows,
  refreshing,
}: {
  rows: SourceTokens[];
  refreshing?: boolean;
}) {
  const theme = useChartTheme();
  const note = missingMeasureNote(rows);

  return (
    <ChartCard
      title="Tokens par source"
      note={note}
      refreshing={refreshing}
      table={
        <table>
          <caption className="sr-only">Consommation de tokens par source</caption>
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Tokens en entrée</th>
              <th scope="col">Tokens de création de cache</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.source}>
                <th scope="row">{row.source}</th>
                <td>{row.inputTokens ? formatAggregate(row.inputTokens) : UNAVAILABLE}</td>
                <td>{row.cacheTokens ? formatAggregate(row.cacheTokens) : UNAVAILABLE}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {rows.length === 0 ? (
        <p className="chart__empty">Aucune source dans ce périmètre.</p>
      ) : (
        <Chart
          option={buildTokensBySourceOption(rows, theme)}
          style={{ height: 260 }}
        />
      )}
    </ChartCard>
  );
}
