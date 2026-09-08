import { useState } from "react";

import type { IndicatorResponse } from "../../../shared/api/types";
import {
  formatAggregateValue,
  formatCoverage,
  isAggregateAvailable,
} from "../utils/formatMetric";

interface KpiCardProps {
  indicator: IndicatorResponse;
}

/**
 * Carte d'un indicateur : valeur ou indisponibilité, jamais un zéro par défaut.
 */
export function KpiCard({ indicator }: KpiCardProps) {
  const [showDefinition, setShowDefinition] = useState(false);
  const { definition, aggregate, mixes_incomparable_sources: mixesSources } = indicator;
  const available = isAggregateAvailable(aggregate);
  const coverage = formatCoverage(aggregate);

  return (
    <article className="kpi-card" aria-labelledby={`kpi-${definition.key}`}>
      <header className="kpi-card__header">
        <h3 id={`kpi-${definition.key}`} className="kpi-card__title">
          {definition.label}
        </h3>
        <button
          type="button"
          className="kpi-card__info"
          aria-expanded={showDefinition}
          aria-controls={`kpi-def-${definition.key}`}
          aria-label="Voir la définition"
          onClick={() => setShowDefinition((open) => !open)}
          title="Voir la définition"
        >
          ?
        </button>
      </header>

      <p className={`kpi-card__value${available ? "" : " kpi-card__value--unavailable"}`}>
        {formatAggregateValue(aggregate)}
        {available && definition.unit !== "%" && definition.unit !== "ms" && (
          <span className="kpi-card__unit"> {definition.unit}</span>
        )}
      </p>

      {!available && (
        <p className="kpi-card__hint">Mesure indisponible sur ce périmètre.</p>
      )}

      {available && aggregate.partial && coverage && (
        <p className="kpi-card__coverage">
          Couverture partielle : {coverage} ({aggregate.covered}/{aggregate.total})
        </p>
      )}

      {mixesSources && (
        <p className="kpi-card__warning" role="note">
          Sources non comparables agrégées — interpréter avec prudence.
        </p>
      )}

      {indicator.sources.length > 0 && (
        <p className="kpi-card__sources">Sources : {indicator.sources.join(", ")}</p>
      )}

      {showDefinition && (
        <dl id={`kpi-def-${definition.key}`} className="kpi-card__definition">
          <div>
            <dt>Calcul</dt>
            <dd>{definition.computation}</dd>
          </div>
          <div>
            <dt>Périmètre</dt>
            <dd>{definition.scope}</dd>
          </div>
          <div>
            <dt>Valeurs manquantes</dt>
            <dd>{definition.missing_values}</dd>
          </div>
        </dl>
      )}
    </article>
  );
}
