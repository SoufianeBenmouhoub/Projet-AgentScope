import type { ActivitySeries, KpiSummary } from "../../../shared/api/types";
import { UNAVAILABLE } from "../formatting";
import {
  partialIndicators,
  toCoverageBySource,
  undatedRecords,
  unavailableIndicators,
  type MeasureCoverage,
} from "./dataQuality";

const PERCENT = new Intl.NumberFormat("fr-FR", { style: "percent", maximumFractionDigits: 0 });

function coverageLabel(measure: MeasureCoverage): string {
  if (!measure.available) {
    return "non publié";
  }
  if (measure.ratio === null) {
    return UNAVAILABLE;
  }
  return `${PERCENT.format(measure.ratio)} (${measure.covered}/${measure.total})`;
}

interface Props {
  summary: KpiSummary;
  activity: ActivitySeries | undefined;
  bySource: { source: string; summary: KpiSummary | undefined }[];
}

/**
 * La qualité des données importées, rendue visible.
 *
 * Ce panneau ne calcule rien de neuf : il rassemble ce que les indicateurs disent déjà
 * d'eux-mêmes — leur couverture réelle, leur indisponibilité et sa raison — et y ajoute ce
 * que les vues temporelles ne peuvent pas montrer.
 *
 * Il existe parce qu'un dashboard qui n'affiche que des chiffres laisse croire qu'ils
 * portent sur tout. Ici, l'écart entre ce qui est mesuré et ce qui est affiché est lui-même
 * une information.
 */
export function DataQualityPanel({ summary, activity, bySource }: Props) {
  const coverage = toCoverageBySource(bySource);
  const unavailable = unavailableIndicators(summary);
  const partial = partialIndicators(summary);
  const undated = activity ? undatedRecords(activity) : [];

  const measures = coverage[0]?.measures ?? [];

  return (
    <section className="quality" aria-label="Qualité des données importées">
      <h3 className="quality__title">Qualité des données importées</h3>

      {measures.length > 0 && coverage.length > 0 && (
        <>
          <h4 className="quality__subtitle">Complétude par source</h4>
          <table className="quality__table">
            <thead>
              <tr>
                <th scope="col">Source</th>
                {measures.map((measure) => (
                  <th scope="col" key={measure.key}>
                    {measure.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {coverage.map((row) => (
                <tr key={row.source}>
                  <th scope="row">{row.source}</th>
                  {row.measures.map((measure) => (
                    <td
                      key={measure.key}
                      className={measure.available ? undefined : "quality__missing"}
                    >
                      {coverageLabel(measure)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="quality__note">
            « non publié » signifie que la source ne fournit pas cette mesure — pas qu'elle
            vaut zéro.
          </p>
        </>
      )}

      {unavailable.length > 0 && (
        <>
          <h4 className="quality__subtitle">Indicateurs indisponibles</h4>
          <dl className="quality__reasons">
            {unavailable.map((entry) => (
              <div key={entry.label}>
                <dt>{entry.label}</dt>
                <dd>{entry.reason}</dd>
              </div>
            ))}
          </dl>
        </>
      )}

      {partial.length > 0 && (
        <>
          <h4 className="quality__subtitle">Indicateurs partiels</h4>
          <dl className="quality__reasons">
            {partial.map((entry) => (
              <div key={entry.label}>
                <dt>{entry.label}</dt>
                <dd>{entry.reason}</dd>
              </div>
            ))}
          </dl>
        </>
      )}

      {undated.length > 0 && (
        <>
          <h4 className="quality__subtitle">Exclus des vues temporelles</h4>
          <ul className="quality__list">
            {undated.map((entry) => (
              <li key={entry.label}>
                {entry.count} {entry.label.toLowerCase()} sans horodatage
              </li>
            ))}
          </ul>
        </>
      )}

      <h4 className="quality__subtitle">Rejets du dernier import</h4>
      <p className="quality__note">
        Non disponible : le bilan d'import n'est pas encore exposé par l'API. Cette section
        listera les enregistrements rejetés et leur explication.
      </p>
    </section>
  );
}
