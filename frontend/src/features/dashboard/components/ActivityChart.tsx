import { useQuery } from "@tanstack/react-query";
import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import { fetchActivitySeries } from "../../../shared/api/metrics";
import type { TraceFilters } from "../../../shared/api/types";

interface ActivityChartProps {
  filters: TraceFilters;
  onDrillDown: (sessionIds: string[], label: string) => void;
}

export function ActivityChart({ filters, onDrillDown }: ActivityChartProps) {
  const { data, isPending, isError } = useQuery({
    queryKey: ["metrics", "activity", filters],
    queryFn: () => fetchActivitySeries(filters),
  });

  const option = useMemo(() => {
    if (!data) {
      return null;
    }

    const days = data.points.map((point) => point.day);

    return {
      tooltip: { trigger: "axis" as const },
      legend: { data: ["Sessions", "Appels modèle", "Appels outils"], bottom: 0 },
      grid: { left: 48, right: 16, top: 24, bottom: 48 },
      xAxis: { type: "category" as const, data: days },
      yAxis: { type: "value" as const, minInterval: 1 },
      series: [
        {
          name: "Sessions",
          type: "bar" as const,
          data: data.points.map((point) => point.sessions),
        },
        {
          name: "Appels modèle",
          type: "line" as const,
          smooth: true,
          data: data.points.map((point) => point.model_calls),
        },
        {
          name: "Appels outils",
          type: "line" as const,
          smooth: true,
          data: data.points.map((point) => point.tool_calls),
        },
      ],
    };
  }, [data]);

  const handleClick = (params: { dataIndex?: number; seriesName?: string }) => {
    if (!data || params.dataIndex === undefined) {
      return;
    }

    const point = data.points[params.dataIndex];
    if (!point || point.session_ids.length === 0) {
      return;
    }

    onDrillDown(point.session_ids, `Activité du ${point.day}`);
  };

  if (isPending) {
    return <p className="status-message">Chargement de l'activité…</p>;
  }

  if (isError) {
    return (
      <p className="status-message status-message--error" role="alert">
        Impossible de charger la série d'activité.
      </p>
    );
  }

  if (!data || data.points.length === 0) {
    return (
      <p className="status-message">
        Aucune activité datée dans le périmètre.
        {data?.has_undated_records && " Des enregistrements sans date existent — voir Qualité."}
      </p>
    );
  }

  return (
    <section className="chart-panel" aria-label="Activité dans le temps">
      <h2 className="section-title">Activité dans le temps</h2>
      <p className="chart-panel__hint">Cliquez sur un point pour filtrer les sessions.</p>
      {option && (
        <ReactECharts
          option={option}
          style={{ height: 320 }}
          onEvents={{ click: handleClick }}
        />
      )}
    </section>
  );
}
