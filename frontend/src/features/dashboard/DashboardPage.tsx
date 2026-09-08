/**
 * Tableau de bord — indicateurs, visualisations et filtres.
 *
 * Les composants métier (KPI, graphiques, drill-down) arrivent dans les étapes suivantes.
 */
export function DashboardPage() {
  return (
    <section className="page">
      <header className="page__header">
        <h1>Dashboard</h1>
        <p className="page__lead">
          Vue d'ensemble des sessions importées : activité, tokens, outils et qualité des
          données.
        </p>
      </header>

      <p className="placeholder">Les indicateurs et graphiques seront branchés ici.</p>
    </section>
  );
}
