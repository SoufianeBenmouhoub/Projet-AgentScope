import { useState } from "react";

import { ActivityChart } from "./components/ActivityChart";
import { DashboardFilters } from "./components/DashboardFilters";
import { DataQualityPanel } from "./components/DataQualityPanel";
import { DrillDownPanel } from "./components/DrillDownPanel";
import { KpiGrid } from "./components/KpiGrid";
import { ToolBreakdownChart } from "./components/ToolBreakdownChart";
import { useDashboardFilters } from "./hooks/useDashboardFilters";

export function DashboardPage() {
  const { filters, setFilters, resetFilters, filterSessionIds } = useDashboardFilters();
  const [drillDown, setDrillDown] = useState<{ label: string; sessionIds: string[] } | null>(
    null,
  );

  const handleDrillDown = (sessionIds: string[], label: string) => {
    setDrillDown({ label, sessionIds });
  };

  return (
    <section className="page">
      <header className="page__header">
        <h1>Dashboard</h1>
        <p className="page__lead">
          Vue d'ensemble des sessions importées : activité, tokens, outils et qualité des
          données.
        </p>
      </header>

      <DashboardFilters filters={filters} onChange={setFilters} onReset={resetFilters} />

      <KpiGrid filters={filters} />

      <div className="charts-grid">
        <ActivityChart filters={filters} onDrillDown={handleDrillDown} />
        <ToolBreakdownChart filters={filters} onDrillDown={handleDrillDown} />
        <DataQualityPanel filters={filters} />
      </div>

      {drillDown && (
        <DrillDownPanel
          label={drillDown.label}
          sessionIds={drillDown.sessionIds}
          onClose={() => setDrillDown(null)}
          onApplyFilter={(sessionIds) => {
            filterSessionIds(sessionIds);
            setDrillDown(null);
          }}
        />
      )}
    </section>
  );
}
