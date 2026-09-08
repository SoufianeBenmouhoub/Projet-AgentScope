import type { ToolBreakdown } from "../../../shared/api/types";
import { formatAggregate } from "../formatting";
import { Chart } from "./Chart";
import { ChartCard } from "./ChartCard";
import { useChartTheme } from "./theme";
import { buildToolBreakdownOption, toBars } from "./toolBreakdownOption";

export function ToolBreakdownChart({
  breakdown,
  refreshing,
}: {
  breakdown: ToolBreakdown;
  refreshing?: boolean;
}) {
  const theme = useChartTheme();
  const bars = toBars(breakdown);

  return (
    <ChartCard
      title="Répartition des appels d'outils"
      refreshing={refreshing}
      table={
        <table>
          <caption className="sr-only">Usage par outil</caption>
          <thead>
            <tr>
              <th scope="col">Outil</th>
              <th scope="col">Appels</th>
              <th scope="col">Part</th>
              <th scope="col">Taux d'erreur</th>
              <th scope="col">Latence médiane</th>
            </tr>
          </thead>
          <tbody>
            {breakdown.usages.map((usage) => (
              <tr key={usage.tool_name}>
                <th scope="row">{usage.tool_name}</th>
                <td>{formatAggregate(usage.calls)}</td>
                <td>{formatAggregate(usage.share)}</td>
                <td>{formatAggregate(usage.error_rate)}</td>
                <td>{formatAggregate(usage.median_latency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {bars.length === 0 ? (
        <p className="chart__empty">Aucun appel d'outil dans ce périmètre.</p>
      ) : (
        <Chart
          option={buildToolBreakdownOption(bars, theme)}
          style={{ height: Math.max(160, bars.length * 30 + 40) }}
        />
      )}
    </ChartCard>
  );
}
