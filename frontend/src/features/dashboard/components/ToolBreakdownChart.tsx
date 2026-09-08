import { useQuery } from "@tanstack/react-query";
import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import { fetchToolBreakdown } from "../../../shared/api/metrics";
import type { TraceFilters } from "../../../shared/api/types";
import { formatAggregateValue } from "../utils/formatMetric";

interface ToolBreakdownChartProps {
  filters: TraceFilters;
  onDrillDown: (sessionIds: string[], label: string) => void;
}

export function ToolBreakdownChart({ filters, onDrillDown }: ToolBreakdownChartProps) {
  const { data, isPending, isError } = useQuery({
    queryKey: ["metrics", "tools", filters],
    queryFn: () => fetchToolBreakdown(filters),
  });

  const option = useMemo(() => {
    if (!data || data.usages.length === 0) {
      return null;
    }

    return {
      tooltip: {
        trigger: "item" as const,
        formatter: (params: { name: string; value: number; percent: number }) =>
          `${params.name}<br/>${params.value} appels (${params.percent.toFixed(1)} %)`,
      },
      legend: { type: "scroll" as const, bottom: 0 },
      series: [
        {
          name: "Outils",
          type: "pie" as const,
          radius: ["35%", "65%"],
          center: ["50%", "45%"],
          data: data.usages.map((usage) => ({
            name: usage.tool_name,
            value: usage.calls.available ? (usage.calls.value ?? 0) : 0,
          })),
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0 },
          },
        },
      ],
    };
  }, [data]);

  const handleClick = (params: { name?: string }) => {
    if (!data || !params.name) {
      return;
    }

    const usage = data.usages.find((item) => item.tool_name === params.name);
    if (!usage || usage.session_ids.length === 0) {
      return;
    }

    onDrillDown(usage.session_ids, `Outil ${usage.tool_name}`);
  };

  if (isPending) {
    return <p className="status-message">Chargement de la répartition des outils…</p>;
  }

  if (isError) {
    return (
      <p className="status-message status-message--error" role="alert">
        Impossible de charger la répartition des outils.
      </p>
    );
  }

  if (!data || data.usages.length === 0) {
    return <p className="status-message">Aucun appel d'outil dans le périmètre.</p>;
  }

  return (
    <section className="chart-panel" aria-label="Répartition des outils">
      <h2 className="section-title">Répartition des outils</h2>
      <p className="chart-panel__meta">
        {data.distinct_tools} outil(s) distinct(s) · {data.tool_calls_total} appel(s)
      </p>
      <p className="chart-panel__hint">Cliquez sur un segment pour filtrer les sessions.</p>
      {option && (
        <ReactECharts
          option={option}
          style={{ height: 320 }}
          onEvents={{ click: handleClick }}
        />
      )}

      <ul className="tool-list">
        {data.usages.slice(0, 5).map((usage) => (
          <li key={usage.tool_name}>
            <button
              type="button"
              className="btn btn--link"
              onClick={() => onDrillDown(usage.session_ids, `Outil ${usage.tool_name}`)}
            >
              {usage.tool_name}
            </button>
            {" — "}
            {formatAggregateValue(usage.calls)} appels
            {usage.error_rate.available && (
              <> · erreurs {formatAggregateValue(usage.error_rate)}</>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
