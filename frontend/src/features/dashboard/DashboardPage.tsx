import { useState } from "react";

import type { Indicator } from "../../shared/api/types";
import { useFilterOptions, useKpiSummary } from "./api";
import "./dashboard.css";
import { FilterBar } from "./FilterBar";
import { isUnfiltered, NO_FILTERS, type TraceFilters } from "./filters";
import { IndicatorCard } from "./IndicatorCard";

/**
 * Y a-t-il seulement quelque chose à explorer ?
 *
 * Les dénombrements sont toujours disponibles : zéro session et zéro appel au modèle
 * signifient réellement qu'il n'y a rien dans le périmètre. Reste à savoir si c'est parce
 * que rien n'a été importé, ou parce que les filtres sont trop restrictifs — l'utilisateur
 * n'a pas la même chose à faire dans les deux cas.
 */
function isScopeEmpty(indicators: Indicator[]): boolean {
  const valueOf = (key: string) =>
    indicators.find((indicator) => indicator.definition.key === key)?.aggregate.value;

  return valueOf("sessions_total") === 0 && valueOf("model_calls_total") === 0;
}

export function DashboardPage() {
  const [filters, setFilters] = useState<TraceFilters>(NO_FILTERS);

  const options = useFilterOptions();
  const summary = useKpiSummary(filters);

  if (summary.isPending) {
    return <p className="dashboard__status">Chargement des indicateurs…</p>;
  }

  if (summary.isError) {
    return (
      <p className="dashboard__status" role="alert">
        Les indicateurs sont indisponibles : l'API ne répond pas.
      </p>
    );
  }

  const nothingImported = options.data?.is_empty ?? false;
  const scopeEmpty = isScopeEmpty(summary.data.indicators);

  return (
    <section className="dashboard">
      <h2>Tableau de bord</h2>

      {options.data && (
        <FilterBar options={options.data} filters={filters} onChange={setFilters} />
      )}

      {nothingImported ? (
        <p className="dashboard__empty">
          Aucune trace n'a encore été importée. Les indicateurs apparaîtront après le premier
          import.
        </p>
      ) : scopeEmpty ? (
        <p className="dashboard__empty">
          {isUnfiltered(filters)
            ? "Aucune trace à afficher."
            : "Aucune trace ne correspond aux filtres actifs. Élargissez le périmètre pour voir des résultats."}
        </p>
      ) : (
        <div className="dashboard__indicators">
          {summary.data.indicators.map((indicator) => (
            <IndicatorCard key={indicator.definition.key} indicator={indicator} />
          ))}
        </div>
      )}
    </section>
  );
}
