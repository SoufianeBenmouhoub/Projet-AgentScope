import { useQuery } from "@tanstack/react-query";

import { fetchActivitySeries, fetchKpiSummary } from "../../../shared/api/metrics";
import type { TraceFilters } from "../../../shared/api/types";
import { formatCoverage } from "../utils/formatMetric";

interface DataQualityPanelProps {
  filters: TraceFilters;
}

/** Rend visible la couverture et les enregistrements non datés. */
export function DataQualityPanel({ filters }: DataQualityPanelProps) {
  const summaryQuery = useQuery({
    queryKey: ["metrics", "summary", filters],
    queryFn: () => fetchKpiSummary(filters),
  });

  const activityQuery = useQuery({
    queryKey: ["metrics", "activity", filters],
    queryFn: () => fetchActivitySeries(filters),
  });

  if (summaryQuery.isPending || activityQuery.isPending) {
    return <p className="status-message">Analyse de la qualité des données…</p>;
  }

  if (summaryQuery.isError || activityQuery.isError) {
    return (
      <p className="status-message status-message--error" role="alert">
        Impossible d'évaluer la qualité des données.
      </p>
    );
  }

  const partialIndicators = summaryQuery.data.indicators.filter(
    (item) => item.aggregate.partial,
  );
  const unavailableIndicators = summaryQuery.data.indicators.filter(
    (item) => !item.aggregate.available,
  );
  const activity = activityQuery.data;

  return (
    <section className="quality-panel" aria-label="Qualité des données">
      <h2 className="section-title">Qualité des données</h2>

      <ul className="quality-list">
        {partialIndicators.length === 0 && unavailableIndicators.length === 0 && (
          <li>Toutes les mesures du périmètre sont complètes.</li>
        )}

        {partialIndicators.map((item) => {
          const coverage = formatCoverage(item.aggregate);
          return (
            <li key={item.definition.key}>
              <strong>{item.definition.label}</strong> — couverture partielle
              {coverage ? ` (${coverage})` : ""} : {item.aggregate.covered}/
              {item.aggregate.total} enregistrements.
            </li>
          );
        })}

        {unavailableIndicators.map((item) => (
          <li key={item.definition.key}>
            <strong>{item.definition.label}</strong> — indisponible sur ce périmètre.
          </li>
        ))}

        {activity.has_undated_records && (
          <li>
            Enregistrements sans date : {activity.undated_sessions} session(s),{" "}
            {activity.undated_model_calls} appel(s) modèle, {activity.undated_tool_calls}{" "}
            appel(s) outil — exclus de la série temporelle.
          </li>
        )}
      </ul>
    </section>
  );
}
