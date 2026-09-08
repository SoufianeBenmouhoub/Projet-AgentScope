import { useQuery } from "@tanstack/react-query";

import { fetchKpiSummary } from "../../../shared/api/metrics";
import type { TraceFilters } from "../../../shared/api/types";
import { KpiCard } from "./KpiCard";

interface KpiGridProps {
  filters: TraceFilters;
}

export function KpiGrid({ filters }: KpiGridProps) {
  const { data, isPending, isError } = useQuery({
    queryKey: ["metrics", "summary", filters],
    queryFn: () => fetchKpiSummary(filters),
  });

  if (isPending) {
    return <p className="status-message">Chargement des indicateurs…</p>;
  }

  if (isError) {
    return (
      <p className="status-message status-message--error" role="alert">
        Impossible de charger les indicateurs.
      </p>
    );
  }

  if (data.indicators.length === 0) {
    return (
      <p className="status-message">
        Aucun indicateur disponible. Importez des traces pour alimenter le dashboard.
      </p>
    );
  }

  return (
    <section aria-label="Indicateurs clés">
      <h2 className="section-title">Indicateurs</h2>
      <div className="kpi-grid">
        {data.indicators.map((indicator) => (
          <KpiCard key={indicator.definition.key} indicator={indicator} />
        ))}
      </div>
    </section>
  );
}
