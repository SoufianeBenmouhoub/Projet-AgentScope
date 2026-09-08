import type { Indicator } from "../../shared/api/types";
import { useKpiSummary } from "./api";
import "./dashboard.css";
import { IndicatorCard } from "./IndicatorCard";

/**
 * Y a-t-il seulement quelque chose à explorer ?
 *
 * Les dénombrements sont toujours disponibles : zéro session et zéro appel au modèle
 * signifient réellement qu'aucune trace n'a été importée. On distingue ce cas d'un
 * dashboard qui affiche des indicateurs vides, parce que l'utilisateur n'a pas la même
 * chose à faire dans les deux situations.
 */
function hasNoTraces(indicators: Indicator[]): boolean {
  const valueOf = (key: string) =>
    indicators.find((indicator) => indicator.definition.key === key)?.aggregate.value;

  return valueOf("sessions_total") === 0 && valueOf("model_calls_total") === 0;
}

export function DashboardPage() {
  const { data, isPending, isError } = useKpiSummary();

  if (isPending) {
    return <p className="dashboard__status">Chargement des indicateurs…</p>;
  }

  if (isError) {
    return (
      <p className="dashboard__status" role="alert">
        Les indicateurs sont indisponibles : l'API ne répond pas.
      </p>
    );
  }

  if (hasNoTraces(data.indicators)) {
    return (
      <section className="dashboard">
        <h2>Tableau de bord</h2>
        <p className="dashboard__empty">
          Aucune trace n'a encore été importée. Les indicateurs apparaîtront après le premier
          import.
        </p>
      </section>
    );
  }

  return (
    <section className="dashboard">
      <h2>Tableau de bord</h2>
      <div className="dashboard__indicators">
        {data.indicators.map((indicator) => (
          <IndicatorCard key={indicator.definition.key} indicator={indicator} />
        ))}
      </div>
    </section>
  );
}
