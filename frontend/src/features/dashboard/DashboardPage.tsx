import { useState } from "react";

import type { Indicator } from "../../shared/api/types";
import {
  useActivitySeries,
  useFilterOptions,
  useKpiSummary,
  useSessionDetail,
  useSessions,
  useSummaryBySource,
  useToolBreakdown,
} from "./api";
import { ActivityChart } from "./charts/ActivityChart";
import { TokensBySourceChart } from "./charts/TokensBySourceChart";
import { toSourceTokens } from "./charts/tokensBySourceOption";
import { ToolBreakdownChart } from "./charts/ToolBreakdownChart";
import "./dashboard.css";
import { FilterBar } from "./FilterBar";
import { isUnfiltered, NO_FILTERS, type TraceFilters } from "./filters";
import { IndicatorCard } from "./IndicatorCard";
import { DataQualityPanel } from "./quality/DataQualityPanel";
import { SessionDetail } from "./sessions/SessionDetail";
import { SessionList } from "./sessions/SessionList";

/** Ce qu'un clic dans un graphique met en sélection, et d'où il vient. */
interface Selection {
  sessionIds: string[];
  origin: string;
}

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
  const [selection, setSelection] = useState<Selection | null>(null);
  const [openSessionId, setOpenSessionId] = useState<string | null>(null);

  const options = useFilterOptions();
  const summary = useKpiSummary(filters);
  const activity = useActivitySeries(filters);
  const tools = useToolBreakdown(filters);

  // Les sources effectivement consultées : celles choisies, ou toutes si aucun choix.
  const sources = filters.sources.length > 0 ? filters.sources : (options.data?.sources ?? []);
  const bySource = useSummaryBySource(sources, filters);

  // La sélection n'entre que dans cette requête : un clic sur une barre montre les sessions
  // concernées, il ne restreint pas les indicateurs de toute la page.
  const sessions = useSessions(
    { ...filters, sessionIds: selection?.sessionIds ?? [] },
    selection !== null,
  );

  const detail = useSessionDetail(openSessionId);

  function select(sessionIds: string[], origin: string) {
    setSelection({ sessionIds, origin });
    setOpenSessionId(null);
  }

  function changeFilters(next: TraceFilters) {
    setFilters(next);
    // Une sélection faite sur un périmètre qu'on vient de changer ne veut plus rien dire.
    setSelection(null);
    setOpenSessionId(null);
  }

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
        <FilterBar options={options.data} filters={filters} onChange={changeFilters} />
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
        <>
          <div className="dashboard__indicators">
            {summary.data.indicators.map((indicator) => (
              <IndicatorCard key={indicator.definition.key} indicator={indicator} />
            ))}
          </div>

          <div className="dashboard__charts">
            {activity.data && (
              <ActivityChart
                series={activity.data}
                refreshing={activity.isFetching}
                onSelect={select}
              />
            )}
            {tools.data && (
              <ToolBreakdownChart
                breakdown={tools.data}
                refreshing={tools.isFetching}
                onSelect={select}
              />
            )}
            {sources.length > 0 && !bySource.isPending && (
              <TokensBySourceChart
                rows={toSourceTokens(bySource.rows)}
                refreshing={bySource.isFetching}
              />
            )}
          </div>

          <p className="dashboard__hint">
            Cliquez sur une journée ou sur un outil pour retrouver les sessions correspondantes.
          </p>

          {selection && sessions.data && (
            <SessionList
              listing={sessions.data}
              origin={selection.origin}
              selectedId={openSessionId}
              onSelect={setOpenSessionId}
              onClear={() => {
                setSelection(null);
                setOpenSessionId(null);
              }}
            />
          )}

          {detail.data && <SessionDetail detail={detail.data} />}

          <DataQualityPanel
            summary={summary.data}
            activity={activity.data}
            bySource={bySource.rows}
          />
        </>
      )}
    </section>
  );
}
